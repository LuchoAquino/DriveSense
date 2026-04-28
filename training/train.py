from ultralytics import YOLO
import torch

if __name__ == '__main__':
    print("CUDA version:", torch.version.cuda)  # Versión de CUDA
    print("cuDNN version:", torch.backends.cudnn.version())  # Versión de cuDNN

    model = YOLO("yolo11n.pt")
    model.train(
        data="data.yaml",
        epochs=50,
        imgsz=640,
        device=0,
        batch=4,
        workers=2,
        amp=False,
        half=False,
        cache=False,
    )
    torch.cuda.empty_cache()


# import torch
# import torchvision

# print(torch.__version__)
# print(torchvision.__version__)
# print(torch.version.cuda)
# print(torchvision.get_image_backend())  # Solo para ver el backend de imágenes

# # Verifica si torchvision está compilado con soporte CUDA
# print(torchvision.ops.nms is not None)
# print(torch.cuda.is_available())