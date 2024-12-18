from rest_framework import viewsets
from rest_framework.decorators import action
from rest_framework.response import Response
from .models import Destination,Account
from .serializers import DestinationSerializer,AccountSerializer
import requests
from rest_framework.views import APIView
from rest_framework import status
from uuid import UUID


class AccountViewSet(viewsets.ModelViewSet):
    queryset = Account.objects.all()
    serializer_class = AccountSerializer

class DestinationViewSet(viewsets.ModelViewSet):
    queryset = Destination.objects.all()
    serializer_class = DestinationSerializer

    @action(detail=False, methods=['GET'])
    def account_destinations(self, request):
        account_id = request.query_params.get('account_id')
        destinations = Destination.objects.filter(account__account_id=account_id)
        serializer = self.get_serializer(destinations, many=True)
        return Response(serializer.data)
    



class IncomingDataView(APIView):
    def validate_uuid(self, uuid_to_validate):
        try:
            UUID(str(uuid_to_validate))
            return True
        except ValueError:
            return False

    def post(self, request):
        secret_token = request.headers.get('CL-X-TOKEN')
        
        if not secret_token:
            return Response(
                {"error": "Un Authenticate - Token Missing"}, 
                status=status.HTTP_401_UNAUTHORIZED
            )
        
        if not self.validate_uuid(secret_token):
            return Response(
                {"error": "Invalid Token Format - Not a valid UUID"}, 
                status=status.HTTP_400_BAD_REQUEST
            )

        try:
            account = Account.objects.get(app_secret_token=secret_token)
        except Account.DoesNotExist:
            return Response(
                {"error": "Invalid Token - Account Not Found"}, 
                status=status.HTTP_401_UNAUTHORIZED
            )
        except ValueError:
            return Response(
                {"error": "Invalid Token Format"}, 
                status=status.HTTP_400_BAD_REQUEST
            )

        if not request.data:
            return Response(
                {"error": "Invalid Data - No Data Received"}, 
                status=status.HTTP_400_BAD_REQUEST
            )
        
        if not isinstance(request.data, dict):
            return Response(
                {"error": "Invalid Data - Must be JSON"}, 
                status=status.HTTP_400_BAD_REQUEST
            )

        destinations = Destination.objects.filter(account=account)
        
        destination_results = []

        for destination in destinations:
            try:
                if destination.http_method == 'GET':
                    response = requests.get(
                        destination.url, 
                        params=request.data, 
                        headers=destination.headers
                    )
                elif destination.http_method == 'POST':
                    response = requests.post(
                        destination.url, 
                        json=request.data, 
                        headers=destination.headers
                    )
                elif destination.http_method == 'PUT':
                    response = requests.put(
                        destination.url, 
                        json=request.data, 
                        headers=destination.headers
                    )
                else:
                    destination_results.append({
                        "url": destination.url,
                        "status": "Error",
                        "message": f"Unsupported HTTP method: {destination.http_method}"
                    })
                    continue

                destination_results.append({
                    "url": destination.url,
                    "status": "Success",
                    "response_code": response.status_code
                })

            except requests.RequestException as e:
                destination_results.append({
                    "url": destination.url,
                    "status": "Error",
                    "message": str(e)
                })
            except Exception as e:
                destination_results.append({
                    "url": destination.url,
                    "status": "Unexpected Error",
                    "message": str(e)
                })

        return Response({
            "status": "Data processed",
            # "destinations": destination_results
        }, status=status.HTTP_200_OK)