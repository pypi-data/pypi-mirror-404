import asyncio
import logging
import sys
import torch
from torch import nn

# import os
# os.environ["GRPC_VERBOSITY"] = "debug"
# os.environ["GRPC_TRACE"] = "all"


from kpu.client import Compute, compute, log_event
import kpu.torch.server

# https://docs.pytorch.org/docs/stable/generated/torch.set_printoptions.html
# https://github.com/pytorch/pytorch/blob/c7e67ec05c4964bcc7033ef43851ee2bb9af422b/torch/_tensor_str.py#L117
torch.set_printoptions(precision=2, threshold=1, edgeitems=2)

logging.basicConfig(
    stream=sys.stdout,
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)

logging.getLogger("kpu.torch.client").setLevel(logging.DEBUG)

# @compute(
#     name="mnist",
#     image="ghcr.io/astefanutti/kpu-torch-server@sha256:388874a0de9fe7b3eba040bb4dc773cedd2937fd03286aa034327642984059b7",
#     # resources={"cpu": "4", "memory": "16Gi", "nvidia.com/gpu": "1"},
#     on_events=log_event,
#     # on_metrics=lambda metrics: print(metrics),
# )
@kpu.torch.server.compute("localhost:50053")
async def main(node: Compute):
    print("PyTorch version: ", torch.__version__)

    # device = node.device("cuda" if torch.cuda.is_available() else "cpu")
    # device = node.device("cuda:0")
    device = node.device("cpu")

    x = torch.randn(2, 2)
    y = x.to(device)
    # print("PRINT START")
    # print(y)
    # print("PRINT END")
    y = y.add(10)
    print(device, y.cpu())


    x = torch.randn(2, 2)
    y = torch.randn(2, 2)

    x_kpu = x.to(device)
    y_kpu = y.to(device)

    z_kpu = x_kpu + y_kpu
    z_expected = x + y

    print(z_expected)
    print(z_kpu.cpu())

    print(torch.allclose(z_kpu.cpu(), z_expected))


    # x = torch.randn(2, 3, 4, requires_grad=True)
    # x_kpu = x.to(device).detach().requires_grad_()
    #
    # y_kpu = x_kpu.reshape(6, 4)
    # loss_kpu = y_kpu.sum()
    # loss_kpu.backward()
    #
    # assert x_kpu.grad is not None
    # assert x_kpu.grad.shape == x.shape


    x = torch.randn(2, 2, requires_grad=True)
    y = torch.randn(2, 2, requires_grad=False)

    x_kpu = x.to(device).detach().requires_grad_()
    y_kpu = y.to(device).detach()

    # Operations with requires_grad=True tensor
    z_kpu = x_kpu + y_kpu
    assert z_kpu.requires_grad

    # Operations with only requires_grad=False tensors
    w_kpu = y_kpu * 2
    assert not w_kpu.requires_grad


    # x = torch.tensor([1.0, 2.0, 3.0, 4.0], device=device)
    # result = x.sum()
    # assert torch.allclose(result.cpu(), torch.tensor(10.0))

    m = nn.Linear(4, 2).to(device)

    # cpu_tensor = torch.randn(50, 50)
    # kpu_tensor = cpu_tensor.to(device)
    # result = torch.matmul(kpu_tensor, kpu_tensor.T)
    # cpu_result = result.cpu()
    # print(cpu_result)
    #
    # x = torch.tensor([1.0, 2.0, 3.0, 4.0], device=device)
    # result = x.sum()
    # print(torch.allclose(result.cpu(), torch.tensor(10.0)))


if __name__ == '__main__':
    asyncio.run(main())
