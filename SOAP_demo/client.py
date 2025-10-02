import requests
import xml.etree.ElementTree as ET

class SOAPClient:
    def __init__(self, endpoint):
        self.endpoint = endpoint
        self.headers = {
            'Content-Type': 'text/xml; charset=utf-8',
            'SOAPAction': ''
        }
    
    def _create_soap_envelope(self, method_name, params):
        """Tạo SOAP envelope"""
        soap_body = f'<tns:{method_name} xmlns:tns="http://example.com/soap/">'
        for key, value in params.items():
            soap_body += f'<tns:{key}>{value}</tns:{key}>'
        soap_body += f'</tns:{method_name}>'
        
        envelope = f"""<?xml version="1.0" encoding="UTF-8"?>
<soap:Envelope xmlns:soap="http://schemas.xmlsoap.org/soap/envelope/"
               xmlns:tns="http://example.com/soap/">
   <soap:Body>
      {soap_body}
   </soap:Body>
</soap:Envelope>"""
        
        print(f"SOAP Request for {method_name}:")
        print(envelope)
        print("-" * 50)
        
        return envelope
    
    def _parse_soap_response(self, response_text):
        """Parse SOAP response và trích xuất kết quả"""
        print(f"Raw SOAP Response:\n{response_text}")
        print("-" * 50)
        
        try:
            # Thử parse XML
            root = ET.fromstring(response_text)
            
            # Tìm phần tử Result trong response
            namespaces = {
                'soap': 'http://schemas.xmlsoap.org/soap/envelope/',
                'tns': 'http://example.com/soap/'
            }
            
            # Thử nhiều cách tìm result
            result_element = root.find('.//tns:Result', namespaces)
            if result_element is None:
                result_element = root.find('.//Result')
            if result_element is None:
                # Tìm trong toàn bộ XML
                for elem in root.iter():
                    if elem.tag.endswith('Result') and elem.text:
                        result_element = elem
                        break
            
            if result_element is not None and result_element.text:
                return result_element.text.strip()
            else:
                # Thử tìm fault string nếu có lỗi
                fault_string = root.find('.//faultstring')
                if fault_string is not None and fault_string.text:
                    return f"Lỗi: {fault_string.text}"
                
                # Debug: in toàn bộ cấu trúc XML
                print("Debug XML structure:")
                for elem in root.iter():
                    print(f"Tag: {elem.tag}, Text: {elem.text}")
                
                return "Không tìm thấy kết quả trong response"
                
        except ET.ParseError as e:
            print(f"XML Parse Error: {e}")
            print(f"Response text that failed to parse: {response_text}")
            return f"Lỗi parse XML: {e}"
        except Exception as e:
            print(f"Unexpected error: {e}")
            return f"Lỗi không xác định: {e}"
    
    def call_method(self, method_name, **params):
        """Gọi phương thức SOAP"""
        soap_envelope = self._create_soap_envelope(method_name, params)
        
        try:
            response = requests.post(
                self.endpoint,
                data=soap_envelope,
                headers=self.headers,
                timeout=10
            )
            
            print(f"HTTP Status Code: {response.status_code}")
            
            if response.status_code == 200:
                result = self._parse_soap_response(response.text)
                return f" {result}"
            else:
                return f" HTTP Error: {response.status_code}\nResponse: {response.text}"
                
        except requests.exceptions.RequestException as e:
            return f" Lỗi kết nối: {e}"
    
    def say_hello(self, name):
        return self.call_method('say_hello', name=name)
    
    def add_numbers(self, a, b):
        return self.call_method('add_numbers', a=a, b=b)
    
    def get_user_info(self, user_id):
        return self.call_method('get_user_info', user_id=user_id)

def main():
    ENDPOINT = "http://localhost:8000/"
    client = SOAPClient(ENDPOINT)
    
    print("=" * 60)
    print("SOAP CLIENT SỬ DỤNG REQUESTS")
    print("=" * 60)
    
    while True:
        print("\n" + "="*50)
        print("DEMO SOAP CLIENT - CHỌN PHƯƠNG THỨC")
        print("="*50)
        print("1. say_hello - Chào hỏi")
        print("2. add_numbers - Cộng hai số")
        print("3. get_user_info - Lấy thông tin user")
        print("4. Thoát")
        print("="*50)
        
        choice = input("Chọn chức năng (1-4): ").strip()
        
        if choice == '1':
            name = input("Nhập tên của bạn: ").strip()
            if name:
                result = client.say_hello(name)
                print(f"\nKết quả: {result}")
            else:
                print("Tên không được để trống!")
                
        elif choice == '2':
            num1 = input("Nhập số thứ nhất: ").strip()
            num2 = input("Nhập số thứ hai: ").strip()
            if num1 and num2:
                result = client.add_numbers(num1, num2)
                print(f"\nKết quả: {result}")
            else:
                print("Số không được để trống!")
                
        elif choice == '3':
            user_id = input("Nhập user ID (1, 2, hoặc 3): ").strip()
            if user_id:
                result = client.get_user_info(user_id)
                print(f"\nKết quả: {result}")
            else:
                print(" User ID không được để trống!")
                
        elif choice == '4':
            print(" Cảm ơn bạn đã sử dụng SOAP Client!")
            break
        else:
            print(" Lựa chọn không hợp lệ! Vui lòng chọn 1-4.")

if __name__ == '__main__':
    main()