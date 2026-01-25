from app.services.scan_service import ScanService

scanner = ScanService()

result = scanner.scan_image("sample.png")  # replace with your image
print(result)
