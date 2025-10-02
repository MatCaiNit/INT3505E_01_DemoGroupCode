from http.server import HTTPServer, BaseHTTPRequestHandler
import xml.etree.ElementTree as ET
import re
from urllib.parse import unquote
import html

class SOAPHandler(BaseHTTPRequestHandler):
    
    def do_GET(self):
        """Xử lý request GET để trả về WSDL"""
        if self.path == '/' or self.path == '/?wsdl':
            wsdl_content = self.generate_wsdl()
            self.send_response(200)
            self.send_header('Content-type', 'text/xml; charset=utf-8')
            self.end_headers()
            self.wfile.write(wsdl_content.encode('utf-8'))
            print("Đã trả về WSDL")
        else:
            self.send_response(404)
            self.end_headers()
    
    def do_POST(self):
        """Xử lý SOAP requests"""
        content_length = int(self.headers['Content-Length'])
        post_data = self.rfile.read(content_length).decode('utf-8')
        
        print(f"Received SOAP Request:\n{post_data}")
        
        try:
            # Parse SOAP request
            response = self.process_soap_request(post_data)
            
            self.send_response(200)
            self.send_header('Content-type', 'text/xml; charset=utf-8')
            self.send_header('Content-Length', str(len(response.encode('utf-8'))))
            self.end_headers()
            self.wfile.write(response.encode('utf-8'))
            
            print(f"Sent SOAP Response:\n{response}")
            
        except Exception as e:
            print(f"Error processing request: {e}")
            error_response = self.create_soap_fault("ServerError", str(e))
            self.send_response(500)
            self.send_header('Content-type', 'text/xml; charset=utf-8')
            self.end_headers()
            self.wfile.write(error_response.encode('utf-8'))
    
    def process_soap_request(self, soap_xml):
        """Xử lý và tạo SOAP response"""
        try:
            # Parse XML để lấy thông tin chính xác hơn
            try:
                root = ET.fromstring(soap_xml)
                namespaces = {
                    'soap': 'http://schemas.xmlsoap.org/soap/envelope/',
                    'tns': 'http://example.com/soap/'
                }
                
                # Tìm method name trong body
                body = root.find('.//soap:Body', namespaces)
                if body is not None:
                    for child in body:
                        # Lấy tên method (bỏ namespace)
                        method_name = child.tag.split('}')[-1] if '}' in child.tag else child.tag
                        
                        if method_name == "say_hello":
                            name_elem = child.find('.//tns:name', namespaces)
                            if name_elem is None:
                                # Thử tìm không namespace
                                name_elem = child.find('.//name')
                            name = name_elem.text if name_elem is not None else "Unknown"
                            result = f"Xin chào {name}! Chào mừng bạn đến với SOAP service."
                            return self.create_soap_response("say_helloResponse", result)
                        
                        elif method_name == "add_numbers":
                            a_elem = child.find('.//tns:a', namespaces)
                            b_elem = child.find('.//tns:b', namespaces)
                            if a_elem is None or b_elem is None:
                                # Thử tìm không namespace
                                a_elem = child.find('.//a')
                                b_elem = child.find('.//b')
                            
                            a = a_elem.text if a_elem is not None else "0"
                            b = b_elem.text if b_elem is not None else "0"
                            
                            try:
                                result_num = float(a) + float(b)
                                result = f"Tổng của {a} + {b} = {result_num}"
                            except ValueError:
                                result = f"Lỗi: Không thể chuyển đổi '{a}' và '{b}' thành số"
                            return self.create_soap_response("add_numbersResponse", result)
                        
                        elif method_name == "get_user_info":
                            user_id_elem = child.find('.//tns:user_id', namespaces)
                            if user_id_elem is None:
                                user_id_elem = child.find('.//user_id')
                            user_id = user_id_elem.text if user_id_elem is not None else "0"
                            user_info = self.get_user_info(user_id)
                            return self.create_soap_response("get_user_infoResponse", user_info)
                
                return self.create_soap_fault("MethodNotFound", "Không tìm thấy phương thức phù hợp")
                
            except ET.ParseError:
                # Fallback sử dụng regex nếu parse XML thất bại
                return self.process_soap_request_regex(soap_xml)
                
        except Exception as e:
            return self.create_soap_fault("ProcessingError", str(e))
    
    def process_soap_request_regex(self, soap_xml):
        """Fallback sử dụng regex để xử lý SOAP request"""
        method_name = self.extract_method_name(soap_xml)
        
        if method_name == "say_hello":
            name = self.extract_parameter(soap_xml, "name")
            result = f"Xin chào {name}! Chào mừng bạn đến với SOAP service."
            return self.create_soap_response("say_helloResponse", result)
        
        elif method_name == "add_numbers":
            a = self.extract_parameter(soap_xml, "a")
            b = self.extract_parameter(soap_xml, "b")
            try:
                result_num = float(a) + float(b)
                result = f"Tổng của {a} + {b} = {result_num}"
            except ValueError:
                result = f"Lỗi: Không thể chuyển đổi '{a}' và '{b}' thành số"
            return self.create_soap_response("add_numbersResponse", result)
        
        elif method_name == "get_user_info":
            user_id = self.extract_parameter(soap_xml, "user_id")
            user_info = self.get_user_info(user_id)
            return self.create_soap_response("get_user_infoResponse", user_info)
        
        else:
            return self.create_soap_fault("MethodNotFound", "Phương thức không được hỗ trợ")
    
    def extract_method_name(self, soap_xml):
        """Trích xuất tên phương thức từ SOAP request (regex fallback)"""
        # Tìm method name trong body
        patterns = [
            r'<soap:Body>\s*<(\w+:)?(\w+)',
            r'<Body>\s*<(\w+:)?(\w+)',
            r'<(\w+:)?(\w+)[\s>].*?<\/(\w+:)?\2>'
        ]
        
        for pattern in patterns:
            match = re.search(pattern, soap_xml, re.DOTALL)
            if match:
                method_name = match.group(2)
                # Loại bỏ các tên không phải method
                if method_name not in ['Envelope', 'Body', 'Header']:
                    return method_name
        return "unknown"
    
    def extract_parameter(self, soap_xml, param_name):
        """Trích xuất tham số từ SOAP request (regex fallback)"""
        # Pattern cho cả có namespace và không có namespace
        patterns = [
            f'<[^>]*:{param_name}[^>]*>(.*?)</[^>]*:{param_name}>',
            f'<{param_name}[^>]*>(.*?)</{param_name}>'
        ]
        
        for pattern in patterns:
            match = re.search(pattern, soap_xml, re.DOTALL)
            if match:
                # Decode HTML entities và xử lý khoảng trắng
                value = match.group(1).strip()
                return unquote(value)
        
        return ""
    
    def get_user_info(self, user_id):
        """Lấy thông tin user (mock data)"""
        users = {
            "1": "Nguyễn Mạnh Quỳnh - Tuổi: 21 - Email: manhquynha3csp@gmail.com",
            "2": "Nguyễn Hoàng Lan - Tuổi: 30 - Email: hlnguyen02@gmail.com", 
            "3": "Lê Thanh Hà - Tuổi: 28 - Email: hathanh_le@gmail.com"
        }
        return users.get(user_id, "Không tìm thấy user với ID này")
    
    def create_soap_response(self, method_response, result):
        """Tạo SOAP response đúng chuẩn"""
        # Escape các ký tự đặc biệt trong XML
        escaped_result = html.escape(str(result))
        
        return f"""<?xml version="1.0" encoding="UTF-8"?>
<soap:Envelope xmlns:soap="http://schemas.xmlsoap.org/soap/envelope/"
               xmlns:tns="http://example.com/soap/">
   <soap:Body>
      <tns:{method_response}>
         <tns:Result>{escaped_result}</tns:Result>
      </tns:{method_response}>
   </soap:Body>
</soap:Envelope>"""
    
    def create_soap_fault(self, fault_code, fault_string):
        """Tạo SOAP fault response"""
        escaped_fault_string = html.escape(str(fault_string))
        
        return f"""<?xml version="1.0" encoding="UTF-8"?>
<soap:Envelope xmlns:soap="http://schemas.xmlsoap.org/soap/envelope/">
   <soap:Body>
      <soap:Fault>
         <faultcode>soap:Server</faultcode>
         <faultstring>{escaped_fault_string}</faultstring>
         <detail>
            <ErrorCode>{fault_code}</ErrorCode>
         </detail>
      </soap:Fault>
   </soap:Body>
</soap:Envelope>"""
    
    def generate_wsdl(self):
        """Tạo WSDL document"""
        return '''<?xml version="1.0" encoding="UTF-8"?>
<definitions name="DemoSOAPService"
             targetNamespace="http://example.com/soap/"
             xmlns="http://schemas.xmlsoap.org/wsdl/"
             xmlns:soap="http://schemas.xmlsoap.org/wsdl/soap/"
             xmlns:tns="http://example.com/soap/"
             xmlns:xsd="http://www.w3.org/2001/XMLSchema">

    <types>
        <xsd:schema targetNamespace="http://example.com/soap/">
            <xsd:element name="say_helloRequest">
                <xsd:complexType>
                    <xsd:sequence>
                        <xsd:element name="name" type="xsd:string"/>
                    </xsd:sequence>
                </xsd:complexType>
            </xsd:element>
            <xsd:element name="say_helloResponse">
                <xsd:complexType>
                    <xsd:sequence>
                        <xsd:element name="Result" type="xsd:string"/>
                    </xsd:sequence>
                </xsd:complexType>
            </xsd:element>
            
            <xsd:element name="add_numbersRequest">
                <xsd:complexType>
                    <xsd:sequence>
                        <xsd:element name="a" type="xsd:string"/>
                        <xsd:element name="b" type="xsd:string"/>
                    </xsd:sequence>
                </xsd:complexType>
            </xsd:element>
            <xsd:element name="add_numbersResponse">
                <xsd:complexType>
                    <xsd:sequence>
                        <xsd:element name="Result" type="xsd:string"/>
                    </xsd:sequence>
                </xsd:complexType>
            </xsd:element>
            
            <xsd:element name="get_user_infoRequest">
                <xsd:complexType>
                    <xsd:sequence>
                        <xsd:element name="user_id" type="xsd:string"/>
                    </xsd:sequence>
                </xsd:complexType>
            </xsd:element>
            <xsd:element name="get_user_infoResponse">
                <xsd:complexType>
                    <xsd:sequence>
                        <xsd:element name="Result" type="xsd:string"/>
                    </xsd:sequence>
                </xsd:complexType>
            </xsd:element>
        </xsd:schema>
    </types>

    <message name="say_helloInput">
        <part name="parameters" element="tns:say_helloRequest"/>
    </message>
    <message name="say_helloOutput">
        <part name="parameters" element="tns:say_helloResponse"/>
    </message>
    
    <message name="add_numbersInput">
        <part name="parameters" element="tns:add_numbersRequest"/>
    </message>
    <message name="add_numbersOutput">
        <part name="parameters" element="tns:add_numbersResponse"/>
    </message>
    
    <message name="get_user_infoInput">
        <part name="parameters" element="tns:get_user_infoRequest"/>
    </message>
    <message name="get_user_infoOutput">
        <part name="parameters" element="tns:get_user_infoResponse"/>
    </message>

    <portType name="DemoSOAPPortType">
        <operation name="say_hello">
            <input message="tns:say_helloInput"/>
            <output message="tns:say_helloOutput"/>
        </operation>
        <operation name="add_numbers">
            <input message="tns:add_numbersInput"/>
            <output message="tns:add_numbersOutput"/>
        </operation>
        <operation name="get_user_info">
            <input message="tns:get_user_infoInput"/>
            <output message="tns:get_user_infoOutput"/>
        </operation>
    </portType>

    <binding name="DemoSOAPBinding" type="tns:DemoSOAPPortType">
        <soap:binding style="document" transport="http://schemas.xmlsoap.org/soap/http"/>
        <operation name="say_hello">
            <soap:operation soapAction="say_hello"/>
            <input>
                <soap:body use="literal"/>
            </input>
            <output>
                <soap:body use="literal"/>
            </output>
        </operation>
        <operation name="add_numbers">
            <soap:operation soapAction="add_numbers"/>
            <input>
                <soap:body use="literal"/>
            </input>
            <output>
                <soap:body use="literal"/>
            </output>
        </operation>
        <operation name="get_user_info">
            <soap:operation soapAction="get_user_info"/>
            <input>
                <soap:body use="literal"/>
            </input>
            <output>
                <soap:body use="literal"/>
            </output>
        </operation>
    </binding>

    <service name="DemoSOAPService">
        <port name="DemoSOAPPort" binding="tns:DemoSOAPBinding">
            <soap:address location="http://localhost:8000/"/>
        </port>
    </service>
</definitions>'''

def run_server():
    server = HTTPServer(('localhost', 8000), SOAPHandler)
    print("=" * 50)
    print("SOAP Server đang chạy trên http://localhost:8000")
    print("WSDL có tại: http://localhost:8000/?wsdl")
    print("Các phương thức hỗ trợ:")
    print("  - say_hello(name)")
    print("  - add_numbers(a, b)") 
    print("  - get_user_info(user_id)")
    print("=" * 50)
    print("Nhấn Ctrl+C để dừng server")
    print("=" * 50)
    
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        print("\nĐang dừng server...")
        server.server_close()
        print("Server đã dừng.")

if __name__ == '__main__':
    run_server()