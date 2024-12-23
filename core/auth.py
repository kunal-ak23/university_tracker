from rest_framework_simplejwt.views import TokenObtainPairView
from rest_framework.permissions import AllowAny
from rest_framework.response import Response
from .models import CustomUser

class CustomLoginView(TokenObtainPairView):
    permission_classes = [AllowAny]
    
    def post(self, request, *args, **kwargs):
        response = super().post(request, *args, **kwargs)
        if response.status_code == 200:
            user = CustomUser.objects.get(email=request.data.get('email') or request.data.get('username'))
            
            # Determine role
            if user.is_superuser:
                role = 'admin'
            elif user.role == 'university_poc':
                role = 'university_poc'
            elif user.role == 'provider_poc':
                role = 'provider_poc'
            else:
                role = 'user'
            
            # Add role and user info to response
            response.data['role'] = role
            response.data['user'] = {
                'id': user.id,
                'email': user.email,
                'first_name': user.first_name,
                'last_name': user.last_name,
            }
        
        return response 