import torch
import torchvision
from torchvision import transforms
from PIL import Image
from io import BytesIO
import requests

def map_imagenet_to_category(label):
    label = label.lower().replace("_", " ")
    
    # 1. Chó
    dog_keywords = ["dog", "retriever", "terrier", "spaniel", "shepherd", "collie", "pug", "chow", "poodle", "husky", "malamute", "rottweiler", "beagle", "bloodhound", "whippet", "greyhound", "mastiff", "pekinese", "dalmatian", "setter", "schnauzer", "chihuahua", "foxhound", "corgi", "pointer", "dane", "hound", "pinscher", "malinois", "spitz"]
    if any(k in label for k in dog_keywords):
        return "dog"
    
    # 2. Mèo
    cat_keywords = ["cat", "tabby", "siamese", "persian", "cougar", "leopard", "lion", "tiger", "jaguar", "panther", "cheetah", "angora"]
    if any(k in label for k in cat_keywords):
        return "cat"
        
    # 3. Xe hơi
    car_keywords = ["cab", "taxi", "sports car", "limousine", "minivan", "convertible", "ambulance", "police van", "beach wagon", "station wagon"]
    if any(k in label for k in car_keywords) or (label.startswith("car ") or " car " in label or label == "car"):
        return "car"
        
    # 4. Cây cối
    tree_keywords = ["tree", "conifer", "fir", "pine", "redwood", "forest", "wood", "leaf", "plant", "woodland", "valley", "lakeside", "alp"]
    if any(k in label for k in tree_keywords):
        return "tree"
        
    return None

class CaptchaV3Solver:
    def __init__(self):
        print("Initializing PyTorch Model MobileNetV3...")
        self.weights = torchvision.models.MobileNet_V3_Large_Weights.DEFAULT
        self.model = torchvision.models.mobilenet_v3_large(weights=self.weights)
        self.model.eval()
        self.class_names = self.weights.meta["categories"]
        
        self.transform = transforms.Compose([
            transforms.Resize(224),
            transforms.CenterCrop(224),
            transforms.ToTensor(),
            transforms.Normalize(mean=[0.485, 0.456, 0.406], std=[0.229, 0.224, 0.225]),
        ])

    def classify_image(self, img_bytes):
        """Phân loại ảnh và trả về danh mục tương ứng (car, dog, cat, tree)"""
        try:
            image = Image.open(BytesIO(img_bytes)).convert("RGB")
            tensor = self.transform(image).unsqueeze(0)
            
            with torch.no_grad():
                output = self.model(tensor)
                probabilities = torch.nn.functional.softmax(output[0], dim=0)
                top_prob, top_catid = torch.topk(probabilities, 1)
                
                class_id = top_catid[0].item()
                raw_label = self.class_names[class_id]
                confidence = top_prob[0].item()
                
                mapped_cat = map_imagenet_to_category(raw_label)
                return mapped_cat, raw_label, confidence
        except Exception as e:
            print(f"Error classifying image: {e}")
            return None, "error", 0.0

    def download_image(self, url):
        try:
            res = requests.get(url, timeout=10)
            if res.status_code == 200:
                return res.content
        except Exception as e:
            print(f"Failed to download image from {url}: {e}")
        return None
