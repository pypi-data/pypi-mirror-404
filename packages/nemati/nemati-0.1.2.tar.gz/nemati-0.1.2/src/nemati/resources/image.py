"""
Image generation resource for Nemati AI SDK.
"""

from typing import BinaryIO, List, Optional, Union

from ..models.image import ImageResponse, GeneratedImage


class Image:
    """
    Image generation resource.
    
    Generate, edit, and upscale images using AI.
    
    Usage:
        # Generate image
        image = client.image.generate(prompt="A sunset over mountains")
        image.save("sunset.png")
        
        # Edit image
        edited = client.image.edit(
            image=open("photo.jpg", "rb"),
            prompt="Make it look like a painting"
        )
    """
    
    def __init__(self, http_client):
        self._http = http_client
    
    def generate(
        self,
        prompt: str,
        negative_prompt: Optional[str] = None,
        size: str = "1024x1024",
        quality: str = "standard",
        style: str = "natural",
        n: int = 1,
        model: str = "stable-diffusion-xl",
        **kwargs,
    ) -> Union[GeneratedImage, List[GeneratedImage]]:
        """
        Generate images from text prompt.
        
        Args:
            prompt: Text description of the image to generate.
            negative_prompt: What to avoid in the image.
            size: Image size. Options: '512x512', '1024x1024', '1024x1792', '1792x1024'.
            quality: Image quality. Options: 'standard', 'hd'.
            style: Image style. Options: 'natural', 'vivid'.
            n: Number of images to generate (1-4).
            model: Model to use for generation.
            **kwargs: Additional model-specific parameters.
        
        Returns:
            GeneratedImage if n=1, or List[GeneratedImage] if n>1.
        
        Example:
            image = client.image.generate(
                prompt="A futuristic city at night, cyberpunk style",
                size="1024x1024",
                quality="hd"
            )
            image.save("city.png")
        """
        payload = {
            "prompt": prompt,
            "size": size,
            "quality": quality,
            "style": style,
            "n": n,
            "model": model,
            **kwargs,
        }
        
        if negative_prompt:
            payload["negative_prompt"] = negative_prompt
        
        response = self._http.request("POST", "/image/generate/", json=payload)
        data = response.get("data", response)
        
        if isinstance(data, list):
            images = [GeneratedImage.from_dict(img) for img in data]
            return images[0] if n == 1 else images
        
        return GeneratedImage.from_dict(data)
    
    def edit(
        self,
        image: BinaryIO,
        prompt: str,
        mask: Optional[BinaryIO] = None,
        strength: float = 0.7,
        size: Optional[str] = None,
        **kwargs,
    ) -> GeneratedImage:
        """
        Edit an existing image (image-to-image).
        
        Args:
            image: The source image file object.
            prompt: Description of the desired changes.
            mask: Optional mask image for inpainting.
            strength: How much to transform the image (0-1). 
                      Higher = more transformation.
            size: Output size. If None, uses source image size.
            **kwargs: Additional parameters.
        
        Returns:
            GeneratedImage with the edited result.
        
        Example:
            edited = client.image.edit(
                image=open("portrait.jpg", "rb"),
                prompt="Add a sunset background",
                strength=0.5
            )
        """
        files = {"image": image}
        if mask:
            files["mask"] = mask
        
        data = {
            "prompt": prompt,
            "strength": strength,
            **kwargs,
        }
        
        if size:
            data["size"] = size
        
        response = self._http.request(
            "POST",
            "/image/edit/",
            files=files,
            data=data,
        )
        return GeneratedImage.from_dict(response.get("data", response))
    
    def upscale(
        self,
        image: BinaryIO,
        scale: int = 2,
        **kwargs,
    ) -> GeneratedImage:
        """
        Upscale an image to higher resolution.
        
        Args:
            image: The image file object to upscale.
            scale: Upscale factor (2 or 4).
            **kwargs: Additional parameters.
        
        Returns:
            GeneratedImage with the upscaled result.
        
        Example:
            upscaled = client.image.upscale(
                image=open("small.jpg", "rb"),
                scale=4
            )
            upscaled.save("large.jpg")
        """
        files = {"image": image}
        data = {"scale": scale, **kwargs}
        
        response = self._http.request(
            "POST",
            "/image/upscale/",
            files=files,
            data=data,
        )
        return GeneratedImage.from_dict(response.get("data", response))
    
    def variations(
        self,
        image: BinaryIO,
        n: int = 1,
        **kwargs,
    ) -> Union[GeneratedImage, List[GeneratedImage]]:
        """
        Generate variations of an existing image.
        
        Args:
            image: The source image file object.
            n: Number of variations to generate (1-4).
            **kwargs: Additional parameters.
        
        Returns:
            GeneratedImage if n=1, or List[GeneratedImage] if n>1.
        """
        files = {"image": image}
        data = {"n": n, **kwargs}
        
        response = self._http.request(
            "POST",
            "/image/variations/",
            files=files,
            data=data,
        )
        data = response.get("data", response)
        
        if isinstance(data, list):
            images = [GeneratedImage.from_dict(img) for img in data]
            return images[0] if n == 1 else images
        
        return GeneratedImage.from_dict(data)
