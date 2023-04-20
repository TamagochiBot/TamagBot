from PIL import Image
import os

def CreatePetImage(wayToBody, wayToHead, wayToWeapon):
    """Пример wayToBody=Body1.png"""
    # weaponImage = Image.open(wayToWeapon)
    weaponImage = Image.open(wayToWeapon)
    bodyImage=Image.open(wayToBody)
    headImage=Image.open(wayToHead)
    bodyWithHeadImage=Image.alpha_composite(bodyImage,headImage)
    petImage=Image.alpha_composite(bodyWithHeadImage,weaponImage)
    return petImage


# image=CreatePetImage("Body1.png","Head1.png","Weapon1.png")
# image.show()
