"""
Challenge Views — SamadhanX
============================
Existing views are preserved.

NEW additions only:
- run_ai_pipeline() helper — called after challenge creation
- ChallengeAIOverrideView — admin accepts or overrides AI result
- ChallengeAIReprocessView — admin triggers re-classification
- DuplicateFlagListView — list duplicate flags for admin review
- DuplicateFlagReviewView — admin confirms or dismisses duplicate flags
"""

import logging
from django.utils import timezone
from rest_framework import generics, status
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView
from django.db.models import Q

from django.shortcuts import get_object_or_404

from accounts.permissions import IsCitizen, IsGovAdmin, IsGovAdminOrHEISPOC
from .models import Challenge, ChallengeMedia, ChallengeStatusHistory, DuplicateFlag
from .serializers import (
    ChallengeSubmitSerializer, ChallengeListSerializer,
    ChallengeDetailSerializer, ChallengeMediaSerializer,
    AIOverrideSerializer, DuplicateFlagSerializer,
)

logger = logging.getLogger(__name__)


# ─── AI Pipeline Helper ───────────────────────────────────────────────────────

def run_ai_pipeline(challenge: Challenge) -> None:
    """
    Runs AI classification + priority calculation for a challenge,
    then saves the result fields.

    This is called synchronously after challenge creation for the MVP.
    It NEVER raises — errors are caught and logged.

    Does NOT overwrite manual_category or manual_priority once set.
    """
    try:
        from services.ai_classifier import classify_challenge
        from services.priority_engine import calculate_priority
        from master_data.models import Category

        district_name = challenge.district.name if challenge.district else ""

        # Gather image paths
        image_paths = []
        for media in challenge.media.filter(media_type='image'):
            if media.file and hasattr(media.file, 'path'):
                image_paths.append(media.file.path)

        # ── 1. AI Classification ──
        cls_result = classify_challenge(challenge.title, challenge.description, district_name, image_paths)

        # Store raw AI result (always, for audit)
        challenge.ai_category_name = cls_result.get('category') or ''
        challenge.ai_confidence = float(cls_result.get('confidence', 0.0))
        challenge.ai_classification_reason = cls_result.get('reason', '')
        challenge.ai_visual_evidence = cls_result.get('visual_evidence', '')
        challenge.classification_source = cls_result.get('source', 'fallback')
        challenge.ai_processed_at = timezone.now()

        # Apply to active category only if admin hasn't overridden yet
        if not challenge.manual_category_id and cls_result.get('category'):
            try:
                cat_obj = Category.objects.get(name=cls_result['category'])
                challenge.category = cat_obj
                # Convert 0–1 confidence to 0–100 integer
                challenge.category_confidence = int(challenge.ai_confidence * 100)
                challenge.category_reason = challenge.ai_classification_reason
            except Category.DoesNotExist:
                logger.warning("AI returned unknown category '%s', skipping category update.", cls_result['category'])

        # ── 2. Priority Calculation ──
        prio_result = calculate_priority(challenge, challenge.ai_visual_evidence)
        challenge.priority_score = prio_result['priority_score']
        challenge.priority_breakdown = prio_result['priority_breakdown']
        challenge.priority_reason = prio_result['priority_reason']

        # Apply computed priority level only if admin hasn't overridden
        if not challenge.manual_priority:
            challenge.priority = prio_result['priority_level']

        # Save all AI fields in one query (skip full model save overhead)
        Challenge.objects.filter(pk=challenge.pk).update(
            ai_category_name=challenge.ai_category_name,
            ai_confidence=challenge.ai_confidence,
            ai_classification_reason=challenge.ai_classification_reason,
            ai_visual_evidence=challenge.ai_visual_evidence,
            classification_source=challenge.classification_source,
            ai_processed_at=challenge.ai_processed_at,
            category=challenge.category,
            category_confidence=challenge.category_confidence,
            category_reason=challenge.category_reason,
            priority=challenge.priority,
            priority_score=challenge.priority_score,
            priority_breakdown=challenge.priority_breakdown,
            priority_reason=challenge.priority_reason,
        )

        logger.info(
            "AI pipeline complete for %s: category=%s (%.0f%%), priority=%s (%.1f)",
            challenge.reference_id,
            challenge.ai_category_name,
            challenge.ai_confidence * 100,
            challenge.priority,
            challenge.priority_score,
        )

        # ── 3. Problem Twin Detection ──
        from .problem_twin_detection import detect_problem_twin
        detect_problem_twin(challenge)

    except Exception as exc:
        logger.error("AI pipeline failed for challenge %s: %s", challenge.pk, exc, exc_info=True)
        # Never let AI failure affect the submission response


# ─── Existing Views (unchanged) ───────────────────────────────────────────────

class ChallengeSubmitView(APIView):
    permission_classes = [IsCitizen]

    def post(self, request):
        serializer = ChallengeSubmitSerializer(data=request.data)
        if not serializer.is_valid():
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

        # Create the challenge first (existing logic preserved)
        from .categorizer import categorize_challenge, compute_priority
        title = serializer.validated_data['title']
        description = serializer.validated_data['description']

        # Initial keyword-based categorization (instant, no external API)
        cat_result = categorize_challenge(title, description)
        initial_priority = compute_priority(title, description, cat_result.get('category'))

        # Resolve category FK
        from master_data.models import Category
        category_obj = None
        if cat_result.get('category'):
            try:
                category_obj = Category.objects.get(name=cat_result['category'])
            except Category.DoesNotExist:
                pass

        challenge = Challenge.objects.create(
            citizen=request.user,
            title=title,
            description=description,
            district=serializer.validated_data['district'],
            location=serializer.validated_data.get('location', ''),
            category=category_obj,
            category_confidence=cat_result.get('confidence', 0),
            category_reason=cat_result.get('reason', ''),
            priority=initial_priority,
            status=Challenge.STATUS_SUBMITTED,
            classification_source='keyword',
        )

        # Handle uploaded media files
        files = request.FILES.getlist('media')
        for f in files:
            media_type = 'image' if f.content_type.startswith('image') else 'document'
            ChallengeMedia.objects.create(
                challenge=challenge,
                file=f,
                media_type=media_type,
            )

        # Record status history
        ChallengeStatusHistory.objects.create(
            challenge=challenge,
            status=Challenge.STATUS_SUBMITTED,
            changed_by=request.user,
            note='Challenge submitted by citizen.',
        )

        # ── Run AI pipeline and duplicate detection in background thread ──
        # This prevents the frontend from timing out while waiting for Gemini API
        import threading
        
        def run_background_tasks(ch_id):
            try:
                # Need to run setup to avoid "Apps aren't loaded yet" in threads sometimes, but django is already loaded here
                ch = Challenge.objects.get(id=ch_id)
                run_ai_pipeline(ch)
                ch.refresh_from_db()
                from .duplicate_detection import detect_duplicates
                detect_duplicates(ch)
            except Exception as e:
                logger.error(f"Background AI task failed for challenge {ch_id}: {e}")

        # Start the background thread
        thread = threading.Thread(target=run_background_tasks, args=(challenge.id,))
        thread.daemon = True
        thread.start()

        return Response(
            ChallengeDetailSerializer(challenge, context={'request': request}).data,
            status=status.HTTP_201_CREATED
        )


class CitizenChallengeListView(generics.ListAPIView):
    permission_classes = [IsCitizen]
    serializer_class = ChallengeListSerializer

    def get_queryset(self):
        return Challenge.objects.filter(citizen=self.request.user).order_by('-created_at')


class AdminChallengeListView(generics.ListAPIView):
    permission_classes = [IsGovAdmin]
    serializer_class = ChallengeListSerializer

    def get_queryset(self):
        qs = Challenge.objects.select_related('citizen', 'assigned_university').order_by('-created_at')
        q = self.request.query_params.get('q', '')
        category = self.request.query_params.get('category', '')
        district = self.request.query_params.get('district', '')
        status_filter = self.request.query_params.get('status', '')
        priority = self.request.query_params.get('priority', '')

        if q:
            qs = qs.filter(Q(title__icontains=q) | Q(reference_id__icontains=q) | Q(district__name__icontains=q))
        if category:
            qs = qs.filter(category__name=category)
        if district:
            qs = qs.filter(district__name__icontains=district)
        if status_filter:
            qs = qs.filter(status=status_filter)
        if priority:
            qs = qs.filter(priority=priority)
        return qs


class AllRolesChallengeListView(generics.ListAPIView):
    """For HEI/Faculty/Industry to see assigned challenges."""
    permission_classes = [IsAuthenticated]
    serializer_class = ChallengeListSerializer

    def get_queryset(self):
        user = self.request.user
        if user.role == 'hei_spoc':
            from universities.models import University
            try:
                uni = University.objects.get(spoc=user)
                return Challenge.objects.filter(assigned_university=uni).order_by('-created_at')
            except University.DoesNotExist:
                return Challenge.objects.none()
        return Challenge.objects.none()


class ChallengeDetailView(generics.RetrieveAPIView):
    permission_classes = [IsAuthenticated]
    serializer_class = ChallengeDetailSerializer

    def get_queryset(self):
        return Challenge.objects.select_related(
            'citizen', 'assigned_university', 'category', 'district',
            'manual_category',
        ).prefetch_related('media', 'status_history__changed_by')

    def get_object(self):
        obj = super().get_object()
        user = self.request.user
        if user.role == 'citizen' and obj.citizen != user:
            from rest_framework.exceptions import PermissionDenied
            raise PermissionDenied('You do not have permission to view this challenge.')
        return obj


class ChallengeCitizenFeedbackView(APIView):
    """Citizen provides feedback on a COMPLETED challenge."""
    permission_classes = [IsAuthenticated]

    def post(self, request, pk):
        try:
            challenge = Challenge.objects.get(pk=pk, citizen=request.user)
        except Challenge.DoesNotExist:
            return Response({'detail': 'Not found.'}, status=status.HTTP_404_NOT_FOUND)

        if challenge.status != 'COMPLETED':
            return Response({'detail': 'Feedback can only be provided for COMPLETED challenges.'}, status=status.HTTP_400_BAD_REQUEST)

        action = request.data.get('action') # 'resolved' or 'not_resolved'
        comments = request.data.get('comments', '')

        if action == 'resolved':
            challenge.routing_note = f"Citizen confirmed resolution. Comments: {comments}"
            challenge.save()
            ChallengeStatusHistory.objects.create(
                challenge=challenge,
                status='COMPLETED',
                note=f"Citizen confirmed resolution. Comments: {comments}",
                changed_by=request.user
            )
            return Response({'status': 'Feedback recorded as resolved.'})
        elif action == 'not_resolved':
            # Reopen challenge
            challenge.status = 'IN_PROGRESS'
            challenge.routing_note = f"Citizen reported issue not resolved. Comments: {comments}"
            challenge.save()
            ChallengeStatusHistory.objects.create(
                challenge=challenge,
                status='IN_PROGRESS',
                note=f"Reopened by Citizen. Comments: {comments}",
                changed_by=request.user
            )
            return Response({'status': 'Challenge reopened as IN_PROGRESS.'})
        else:
            return Response({'detail': 'Invalid action. Must be resolved or not_resolved.'}, status=status.HTTP_400_BAD_REQUEST)


class ChallengeReviewView(APIView):
    """Admin marks a challenge as UNDER_REVIEW."""
    permission_classes = [IsGovAdmin]

    def post(self, request, pk):
        try:
            challenge = Challenge.objects.get(pk=pk)
        except Challenge.DoesNotExist:
            return Response({'detail': 'Not found.'}, status=status.HTTP_404_NOT_FOUND)

        if challenge.status != Challenge.STATUS_SUBMITTED:
            return Response({'detail': 'Challenge is not in SUBMITTED state.'}, status=400)

        challenge.status = Challenge.STATUS_UNDER_REVIEW
        challenge.save()

        ChallengeStatusHistory.objects.create(
            challenge=challenge,
            status=Challenge.STATUS_UNDER_REVIEW,
            changed_by=request.user,
            note=request.data.get('note', 'Under review by government administrator.'),
        )

        return Response(ChallengeDetailSerializer(challenge, context={'request': request}).data)


class ChallengeRouteView(APIView):
    """Admin routes a challenge to a university."""
    permission_classes = [IsGovAdmin]

    def post(self, request, pk):
        from universities.models import University
        try:
            challenge = Challenge.objects.get(pk=pk)
        except Challenge.DoesNotExist:
            return Response({'detail': 'Not found.'}, status=status.HTTP_404_NOT_FOUND)

        university_id = request.data.get('university_id')
        note = request.data.get('note', '')

        if not university_id:
            return Response({'detail': 'university_id is required.'}, status=400)

        try:
            university = University.objects.get(pk=university_id)
        except University.DoesNotExist:
            return Response({'detail': 'University not found.'}, status=404)

        challenge.assigned_university = university
        challenge.status = Challenge.STATUS_ROUTED
        challenge.routing_note = note
        challenge.save()

        ChallengeStatusHistory.objects.create(
            challenge=challenge,
            status=Challenge.STATUS_ROUTED,
            changed_by=request.user,
            note=f'Routed to {university.name}. {note}',
        )

        from master_data.utils import log_audit
        log_audit(
            user=request.user,
            action='Routed Challenge',
            entity_type='Challenge',
            entity_id=challenge.reference_id,
            new_value=f'University: {university.name}'
        )

        return Response(ChallengeDetailSerializer(challenge, context={'request': request}).data)


class ChallengePriorityUpdateView(APIView):
    """Admin can override priority (existing endpoint)."""
    permission_classes = [IsGovAdmin]

    def patch(self, request, pk):
        try:
            challenge = Challenge.objects.get(pk=pk)
        except Challenge.DoesNotExist:
            return Response({'detail': 'Not found.'}, status=404)

        priority = request.data.get('priority')
        if priority not in ('LOW', 'MEDIUM', 'HIGH'):
            return Response({'detail': 'Invalid priority.'}, status=400)

        prev_priority = challenge.priority
        challenge.priority = priority
        challenge.manual_priority = priority
        challenge.save(update_fields=['priority', 'manual_priority', 'updated_at'])

        from master_data.utils import log_audit
        log_audit(
            user=request.user,
            action='Priority Override',
            entity_type='Challenge',
            entity_id=challenge.reference_id,
            previous_value=f'priority={prev_priority}',
            new_value=f'priority={priority} (manual override)'
        )

        return Response({'priority': challenge.priority})


# ─── NEW: AI Override View ────────────────────────────────────────────────────

class ChallengeAIOverrideView(APIView):
    """
    Admin can accept AI result or override category/priority.

    POST /challenges/<pk>/ai-override/
    Body:
        { "action": "accept" }
        or
        { "action": "override", "category_name": "...", "priority": "HIGH", "override_reason": "..." }
    """
    permission_classes = [IsGovAdmin]

    def post(self, request, pk):
        try:
            challenge = Challenge.objects.get(pk=pk)
        except Challenge.DoesNotExist:
            return Response({'detail': 'Not found.'}, status=404)

        action = request.data.get('action', 'accept')

        if action == 'accept':
            # Persist who accepted and when — survives browser refresh
            challenge.ai_accepted_by = request.user
            challenge.ai_accepted_at = timezone.now()
            # Clear any previous manual overrides — AI result is now the official one
            challenge.manual_category = None
            challenge.manual_priority = ''
            challenge.save(update_fields=[
                'ai_accepted_by', 'ai_accepted_at',
                'manual_category', 'manual_priority', 'updated_at'
            ])

            from master_data.utils import log_audit
            log_audit(
                user=request.user,
                action='Accepted AI Classification',
                entity_type='Challenge',
                entity_id=challenge.reference_id,
                new_value=f'category={challenge.ai_category_name}, priority={challenge.priority}'
            )
            return Response(ChallengeDetailSerializer(challenge, context={'request': request}).data)

        elif action == 'override':
            ser = AIOverrideSerializer(data=request.data)
            if not ser.is_valid():
                return Response(ser.errors, status=400)

            from master_data.models import Category
            update_fields = ['updated_at']
            prev_category = challenge.category.name if challenge.category else ''
            prev_priority = challenge.priority

            # Category override
            category_name = ser.validated_data.get('category_name', '').strip()
            if category_name:
                try:
                    cat_obj = Category.objects.get(name=category_name)
                    challenge.manual_category = cat_obj
                    challenge.category = cat_obj
                    challenge.category_reason = (
                        ser.validated_data.get('override_reason', '')
                        or f"Manual override by admin."
                    )
                    update_fields += ['manual_category', 'category', 'category_reason']
                except Category.DoesNotExist:
                    return Response({'detail': f'Category "{category_name}" not found.'}, status=400)

            # Priority override
            priority_val = ser.validated_data.get('priority', '').strip()
            if priority_val:
                challenge.manual_priority = priority_val
                challenge.priority = priority_val
                update_fields += ['manual_priority', 'priority']

            # Override revokes any prior acceptance
            challenge.ai_accepted_by = None
            challenge.ai_accepted_at = None
            update_fields += ['ai_accepted_by', 'ai_accepted_at']

            challenge.save(update_fields=update_fields)

            from master_data.utils import log_audit
            log_audit(
                user=request.user,
                action='Admin AI Override',
                entity_type='Challenge',
                entity_id=challenge.reference_id,
                previous_value=f'category={prev_category}, priority={prev_priority}',
                new_value=(
                    f'category={category_name or prev_category}, '
                    f'priority={priority_val or prev_priority}. '
                    f'Reason: {ser.validated_data.get("override_reason", "")}'
                )
            )

            challenge.refresh_from_db()
            return Response(ChallengeDetailSerializer(challenge, context={'request': request}).data)

        return Response({'detail': 'Invalid action. Use "accept" or "override".'}, status=400)


# ─── NEW: AI Reprocess View ───────────────────────────────────────────────────

class ChallengeAIReprocessView(APIView):
    """
    Admin triggers re-classification of a challenge.

    POST /challenges/<pk>/ai-reprocess/
    """
    permission_classes = [IsGovAdmin]

    def post(self, request, pk):
        try:
            challenge = Challenge.objects.get(pk=pk)
        except Challenge.DoesNotExist:
            return Response({'detail': 'Not found.'}, status=404)

        # Clear manual overrides AND acceptance before reprocessing
        challenge.manual_category = None
        challenge.manual_priority = ''
        challenge.ai_accepted_by = None
        challenge.ai_accepted_at = None
        challenge.save(update_fields=[
            'manual_category', 'manual_priority',
            'ai_accepted_by', 'ai_accepted_at', 'updated_at'
        ])

        run_ai_pipeline(challenge)
        challenge.refresh_from_db()

        from master_data.utils import log_audit
        log_audit(
            user=request.user,
            action='Triggered AI Reprocess',
            entity_type='Challenge',
            entity_id=challenge.reference_id,
            new_value=f'category={challenge.ai_category_name}, priority={challenge.priority}'
        )

        return Response(ChallengeDetailSerializer(challenge, context={'request': request}).data)


# ─── NEW: Duplicate Detection Review Views ────────────────────────────────────

class DuplicateFlagListView(generics.ListAPIView):
    """
    GET /api/duplicate-flags/?status=pending_review
    Lists duplicate flags for gov_admin review.
    Includes full challenge details for side-by-side comparison.
    Uses select_related to avoid N+1 queries.
    """
    permission_classes = [IsGovAdmin]
    serializer_class = DuplicateFlagSerializer

    def get_queryset(self):
        qs = DuplicateFlag.objects.select_related(
            'challenge_a__citizen',
            'challenge_a__district',
            'challenge_a__category',
            'challenge_a__assigned_university',
            'challenge_b__citizen',
            'challenge_b__district',
            'challenge_b__category',
            'challenge_b__assigned_university',
            'reviewed_by',
        )
        status_filter = self.request.query_params.get('status')
        if status_filter:
            qs = qs.filter(status=status_filter)
        return qs


class DuplicateFlagReviewView(APIView):
    """
    PATCH /api/duplicate-flags/{id}/review/
    body: { "decision": "confirmed_duplicate" | "not_duplicate" }
    Gov admin only.
    """
    permission_classes = [IsGovAdmin]

    def patch(self, request, pk):
        flag = get_object_or_404(DuplicateFlag, pk=pk)
        decision = request.data.get('decision')

        if decision not in ('confirmed_duplicate', 'not_duplicate'):
            return Response(
                {'detail': 'Invalid decision. Use "confirmed_duplicate" or "not_duplicate".'},
                status=status.HTTP_400_BAD_REQUEST,
            )

        flag.status = decision
        flag.reviewed_by = request.user
        flag.reviewed_at = timezone.now()
        return Response(DuplicateFlagSerializer(flag).data)


# ─── NEW: Problem Twin Views ──────────────────────────────────────────────────

from rest_framework import viewsets
from rest_framework.decorators import action
from .models import ProblemTwin
from .serializers import ProblemTwinSerializer

class ProblemTwinViewSet(viewsets.ModelViewSet):
    """
    API for managing Problem Twins.
    Gov admins have full access.
    """
    permission_classes = [IsGovAdmin]
    serializer_class = ProblemTwinSerializer
    queryset = ProblemTwin.objects.all().select_related('category', 'district').prefetch_related('linked_challenges')

    @action(detail=True, methods=['post'])
    def accept_report(self, request, pk=None):
        twin = self.get_object()
        report_id = request.data.get('report_id')
        challenge = get_object_or_404(Challenge, pk=report_id, problem_twin=twin)
        
        challenge.twin_association_status = Challenge.TWIN_STATUS_ACCEPTED
        challenge.save(update_fields=['twin_association_status'])
        
        from master_data.utils import log_audit
        log_audit(
            user=request.user,
            action='Accepted Twin Association',
            entity_type='Challenge',
            entity_id=challenge.reference_id,
            new_value=f'Twin: {twin.reference_id}'
        )
        return Response(self.get_serializer(twin).data)

    @action(detail=True, methods=['post'])
    def reject_report(self, request, pk=None):
        twin = self.get_object()
        report_id = request.data.get('report_id')
        challenge = get_object_or_404(Challenge, pk=report_id, problem_twin=twin)
        
        challenge.twin_association_status = Challenge.TWIN_STATUS_REJECTED
        challenge.problem_twin = None
        challenge.save(update_fields=['twin_association_status', 'problem_twin'])
        
        from master_data.utils import log_audit
        log_audit(
            user=request.user,
            action='Rejected Twin Association',
            entity_type='Challenge',
            entity_id=challenge.reference_id,
            new_value='Removed from Twin'
        )
        return Response(self.get_serializer(twin).data)
