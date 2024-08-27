from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework import status
from users.models import CustomUser
from .serializers import CustomUserTeacherSerializer, CustomUserStudentSerializer


@api_view(["GET"])
@permission_classes([IsAuthenticated])
def get_own_user_details_view(request):
    #
    # if request.user.username != username:
    #     return Response({"error": "You are not authorized to access this data."}, status = status.HTTP_403_FORBIDDEN)
    if request.user.is_teacher:
        user_serializer = CustomUserTeacherSerializer(request.user)
        return Response(user_serializer.data)
    elif request.user.is_student:
        user_serializer = CustomUserStudentSerializer(request.user)
        return Response(user_serializer.data)

    
    