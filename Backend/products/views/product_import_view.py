from rest_framework import status
from rest_framework.parsers import MultiPartParser
from rest_framework.response import Response
from rest_framework.views import APIView

from core.permissions import IsAdminRole
from products.csv_import import CsvImportError, import_products_from_csv


class ProductImportView(APIView):
    """
    POST /api/products/import/   (Admin only, multipart form with a "file" field)

    Success (201): {"message": ..., "imported": 3, "product_codes": [...]}
    Failure (400): {"error": ..., "row_errors": [{"row": 3, "errors": ["price: ..."]}]}
    On failure nothing is saved.
    """

    permission_classes = [IsAdminRole]
    parser_classes = [MultiPartParser]

    def post(self, request):
        uploaded_file = request.FILES.get("file")
        if uploaded_file is None:
            return Response({"error": "Choose a CSV file to upload."}, status=status.HTTP_400_BAD_REQUEST)
        if not uploaded_file.name.lower().endswith(".csv"):
            return Response({"error": "Only .csv files can be imported."}, status=status.HTTP_400_BAD_REQUEST)

        try:
            products = import_products_from_csv(uploaded_file, request.user)
        except CsvImportError as error:
            return Response({"error": error.message, "row_errors": error.row_errors},
                            status=status.HTTP_400_BAD_REQUEST)

        return Response(
            {
                "message": f"Imported {len(products)} product(s).",
                "imported": len(products),
                "product_codes": [product.product_code for product in products],
            },
            status=status.HTTP_201_CREATED,
        )
