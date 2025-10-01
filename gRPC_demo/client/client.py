import grpc
from code_gen import service_pb2, service_pb2_grpc

def run():
    channel = grpc.insecure_channel('localhost:50051')
    stub = service_pb2_grpc.CalculateStub(channel)

    print("===== MENU =====")
    print("1. Bình phương 1 số")
    print("2. Cộng 2 số")
    choice = input("Chọn chức năng: ").strip()
    
    if choice == '1':
        num = int(input("Nhập số: "))
        response = stub.SquareNumber(service_pb2.NumberRequest(value=num))
        print(f"{num} bình =", response.result)
    elif choice == '2':
        a = int(input("Nhập số a: "))
        b = int(input("Nhập số b: "))
        response = stub.AddNumbers(service_pb2.AddRequest(a=a, b=b))
        print(f"{a} + {b} =", response.result)
    else:
        print("Lựa chọn không hợp lệ.")

if __name__ == "__main__":
    run()
