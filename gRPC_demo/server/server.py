import grpc
from concurrent import futures
import time

from code_gen import service_pb2, service_pb2_grpc

class CalculateService(service_pb2_grpc.CalculateServicer):
    def SquareNumber(self, request, context):
        return service_pb2.NumberReply(result=request.value * request.value)

    def AddNumbers(self, request, context):
        return service_pb2.NumberReply(result=request.a + request.b)

def serve():
    server = grpc.server(futures.ThreadPoolExecutor(max_workers=10))
    service_pb2_grpc.add_CalculateServicer_to_server(CalculateService(), server)
    server.add_insecure_port('[::]:50051')
    server.start()
    print("Calculator trên cổng 50051...")
    try:
        while True:
            time.sleep(86400)
    except KeyboardInterrupt:
        server.stop(0)

if __name__ == "__main__":
    serve()
