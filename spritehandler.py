from enum import Enum
import json
import math
from PIL import Image
import os
import os.path
from PyQt6.QtWidgets import *
import copy

class SpritePackingRotation(Enum):
    NONE = 0
    FLIP_HORIZONTAL = 1
    FLIP_VERTICAL = 2
    ROTATE_180 = 3
    ROTATE_90 = 4

class spriteHandler:
    dataArray = []
    categories = {}
    animationsList = []
    basepath = ""
    savedOutputFolder = ""
    
    spriteAtlases = {}
    
    atlasImgCache = {}

    spriteIDs = []
    spriteX = []
    spriteY = []
    spriteXR = []
    spriteYR = []
    spriteW = []
    spriteH = []
    spriteFlipped = []
    spritePath = []
    spriteCollection = []
    spriteRotate = []
    spritePathPoints = []

    duplicatesHashList = []
    duplicatesList = []
    duplicatesCache = {}
    duplicatesHashCache = {}
    duplicatesData = {}
    
    outputLog = None



    @staticmethod
    def loadSpriteInfo(files):
        categories = []
        spriteHandler.spriteAtlases = {}
        spriteHandler.duplicatesCache = {}
        spriteHandler.duplicatesHashCache = {}
        spriteHandler.duplicatesData = {}
        spriteHandler.dataArray = []
        for file in files:
            io = open(file, "r")
            data = json.load(io)
            spriteHandler.dataArray.append(data)
            spriteCollectionList = []
            [
                spriteCollectionList.append(x)
                for x in data["scollectionname"]
                if x not in spriteCollectionList
            ]
            categories += spriteCollectionList
            
            # Get Base Atlases
            atlas_path = os.path.dirname(file)
            atlas_files = os.listdir(atlas_path)
            for collection in spriteCollectionList:
                if (collection + ".png") in atlas_files:
                    spriteHandler.spriteAtlases[collection] = atlas_path + "/" + collection + ".png"
            
            # Cache Duplicate List
            # TODO make sure lengths match and keys exist, may crash if keys don't exist
            for i in range(min(len(data["scollectionname"]), len(data["sx"]), len(data["sy"]), len(data["swidth"]), len(data["sheight"]), len(data["spath"]))):
                key_items = [
                    str(data["scollectionname"][i]),
                    "(", str(data["sx"][i]), ",", str(data["sy"][i]), ")",
                    str(data["swidth"][i]), "x", str(data["sheight"][i])
                ]
                sprite_key = " ".join(key_items)
                if not (sprite_key in spriteHandler.duplicatesCache):
                    spriteHandler.duplicatesCache[sprite_key] = []
                    spriteHandler.duplicatesData[sprite_key] = {
                        "collection": data["scollectionname"][i],
                        "x": data["sx"][i],
                        "y": data["sy"][i],
                        "width": data["swidth"][i],
                        "height": data["sheight"][i],
                        "flipped": data["sfilpped"][i]
                    }
                spriteHandler.duplicatesCache[sprite_key].append(data["spath"][i])
        
        finalCategories = []
        [finalCategories.append(x) for x in categories if x not in finalCategories]
        # print("here")
        # print(finalCategories)
        # print(spriteHandler.spriteAtlases)
        spriteHandler.categories.clear()
        for category in finalCategories:
            spriteHandler.categories[category] = True
        return finalCategories



    @staticmethod
    def loadAnimations(filter):
        spriteHandler.spriteIDs = []
        spriteHandler.spriteX = []
        spriteHandler.spriteY = []
        spriteHandler.spriteXR = []
        spriteHandler.spriteYR = []
        spriteHandler.spriteW = []
        spriteHandler.spriteH = []
        spriteHandler.spriteFlipped = []
        spriteHandler.spritePath = []
        spriteHandler.spriteCollection = []
        spriteHandler.spriteRotate = []
        spriteHandler.spritePathPoints = []
        for data in spriteHandler.dataArray:
            spriteHandler.spriteIDs += data["sid"]
            spriteHandler.spriteX += data["sx"]
            spriteHandler.spriteY += data["sy"]
            spriteHandler.spriteXR += data["sxr"]
            spriteHandler.spriteYR += data["syr"]
            spriteHandler.spriteW += data["swidth"]
            spriteHandler.spriteH += data["sheight"]
            spriteHandler.spriteFlipped += data["sfilpped"]
            spriteHandler.spritePath += data["spath"]
            spriteHandler.spriteCollection += data["scollectionname"]
            
            if data.get("srotate") is not None and data.get("srotate") != "":
                spriteHandler.spriteRotate += data["srotate"]
            if data.get("spathPoints") is not None and data.get("spathPoints") != "":
                spriteHandler.spritePathPoints += data["spathPoints"]
                
        for i in reversed(range(0, len(spriteHandler.spriteCollection))):
            if (not spriteHandler.categories[spriteHandler.spriteCollection[i]]) or (
                str.casefold(filter) not in str.casefold(spriteHandler.spritePath[i])
            ):
                del spriteHandler.spriteIDs[i]
                del spriteHandler.spriteX[i]
                del spriteHandler.spriteY[i]
                del spriteHandler.spriteXR[i]
                del spriteHandler.spriteYR[i]
                del spriteHandler.spriteW[i]
                del spriteHandler.spriteH[i]
                del spriteHandler.spriteFlipped[i]
                del spriteHandler.spritePath[i]
                del spriteHandler.spriteCollection[i]

                if i < len(spriteHandler.spriteRotate):
                    del spriteHandler.spriteRotate[i]
                if i < len(spriteHandler.spritePathPoints):
                    del spriteHandler.spritePathPoints[i]
        animations = []
        for path in spriteHandler.spritePath:
            if os.path.basename(os.path.dirname(path)) not in animations:
                animations.append(os.path.basename(os.path.dirname(path)))
        spriteHandler.animationsList = copy.copy(animations)
        return animations



    @staticmethod
    def loadSprites(animation):
        sprites = []
        for path in spriteHandler.spritePath:
            if os.path.basename(os.path.dirname(path)) == animation:
                sprites.append(os.path.basename(path))
        return sprites



    @staticmethod
    def packSprites(outputDir):
        spriteCollectionList = list(spriteHandler.categories.keys())
        for j in range(0, len(spriteCollectionList)):
            current_collection = spriteCollectionList[j]
            if spriteHandler.categories[current_collection]:
                spriteHandler.outputLog.appendPlainText("Packing: " + current_collection)
                spriteHandler.outputLog.repaint()
                maxW = 0
                maxH = 0
                # print("SPRITE COLLECTION: ", spriteHandler.spriteCollection)
                # print("SPRITE COLLECTION LIST: ", spriteCollectionList)
                # print(spriteHandler.spriteIDs)
                for i in range(0, len(spriteHandler.spriteIDs)):
                    # print(spriteHandler.spriteCollection[i])
                    # print(spriteCollectionList[j])
                    if spriteHandler.spriteCollection[i] == current_collection:
                        if spriteHandler.spriteFlipped[i]:
                            maxW = max(
                                maxW,
                                spriteHandler.spriteX[i] + spriteHandler.spriteH[i],
                            )
                            maxH = max(
                                maxH,
                                spriteHandler.spriteY[i] + spriteHandler.spriteW[i],
                            )
                            # print("flipped:")
                            # print(maxH)
                        else:
                            maxW = max(
                                maxW,
                                spriteHandler.spriteX[i] + spriteHandler.spriteW[i],
                            )
                            maxH = max(
                                maxH,
                                spriteHandler.spriteY[i],
                            )
                            # print("not flipped:")
                            # print(maxH)
                #print(maxW)
                #print(maxH)
                
                atlas_base_path = spriteHandler.getBaseAtlasPath(current_collection)
                atlas_base_load = spriteHandler.attemptToLoadImageFile(atlas_base_path)
                if not (atlas_base_load["img"] is None):
                    maxW = max(maxW, atlas_base_load["img"].width)
                    maxH = max(maxH, atlas_base_load["img"].height)
                
                if not (maxH > 1 and maxW > 1):
                    spriteHandler.outputLog.appendPlainText("(Skip) Size Error - " + current_collection)
                    spriteHandler.outputLog.repaint()
                else:
                    maxW = 2 ** math.ceil(math.log2(maxW - 1))
                    maxH = 2 ** math.ceil(math.log2(maxH - 1))
                    # print(maxW)
                    # print(maxH)

                    out = Image.new("RGBA", (maxW, maxH), (0, 0, 0, 0))
                    
                    if atlas_base_load["img"] is None:
                        spriteHandler.outputLog.appendPlainText("(Skip) No Base Atlas - " + current_collection)
                        spriteHandler.outputLog.repaint()
                    else:
                        out.paste(atlas_base_load["img"])

                    for i in range(0, len(spriteHandler.spriteIDs)):
                        if spriteHandler.spriteCollection[i] == current_collection:
                            img_path = spriteHandler.basepath + "/" + spriteHandler.spritePath[i]
                            img_load = spriteHandler.attemptToLoadImageFile(img_path)
                            if img_load["img"] is None:
                                match img_load["err"]:
                                    case "FileNotFound":
                                        spriteHandler.outputLog.appendPlainText("(Skip) Missing - " + spriteHandler.spritePath[i])
                                    case _:
                                        spriteHandler.outputLog.appendPlainText("(Skip) Error - " + spriteHandler.spritePath[i])
                                spriteHandler.outputLog.repaint()
                                continue;
                            im = img_load["img"]
                            im = im.crop(
                                (
                                    spriteHandler.spriteXR[i],
                                    im.size[1]
                                    - spriteHandler.spriteYR[i]
                                    - spriteHandler.spriteH[i],
                                    spriteHandler.spriteXR[i] + spriteHandler.spriteW[i],
                                    im.size[1] - spriteHandler.spriteYR[i],
                                )
                            )

                            # TK2D
                            if spriteHandler.spriteRotate == []:
                                if spriteHandler.spriteFlipped[i] == True:
                                    x = spriteHandler.spriteX[i]
                                    y = (
                                        out.size[1]
                                        - spriteHandler.spriteY[i]
                                        - spriteHandler.spriteW[i]
                                    )
                                else:
                                    x = spriteHandler.spriteX[i]
                                    y = (
                                        out.size[1]
                                        - spriteHandler.spriteY[i]
                                        - spriteHandler.spriteH[i]
                                    )

                                if spriteHandler.spriteFlipped[i]:
                                    im = im.rotate(90, expand=True)
                                    im = im.transpose(Image.FLIP_LEFT_RIGHT)

                                # Texture2D
                            else:
                                x = spriteHandler.spriteX[i]
                                y = (
                                    out.size[1]
                                    - spriteHandler.spriteY[i]
                                    - spriteHandler.spriteH[i]
                                )

                                packing_rotation = spriteHandler.spriteRotate[i]
                                match packing_rotation:
                                    case SpritePackingRotation.FLIP_HORIZONTAL.value:
                                        im = im.transpose(Image.FLIP_LEFT_RIGHT) 
                                    case SpritePackingRotation.FLIP_VERTICAL.value:
                                        im = im.transpose(Image.FLIP_TOP_BOTTOM) 
                                    case SpritePackingRotation.ROTATE_180.value:
                                        im = im.rotate(180, expand=True)
                                    case SpritePackingRotation.ROTATE_90.value:
                                        im = im.rotate(90, expand=True)
                        

                                # # out.paste(im, (x, y))
                                # # 逐像素檢查並貼上非透明像素
                                # for px in range(im.size[0]):
                                #     for py in range(im.size[1]):
                                #         pixel = im.getpixel((px, py))
                                #         if len(pixel) == 4 and pixel[3] > 0:  # 檢查 alpha 通道
                                #             out_x = x + px
                                #             out_y = y + py
                                #             if 0 <= out_x < out.size[0] and 0 <= out_y < out.size[1]:
                                #                 out.putpixel((out_x, out_y), pixel)

                                # out.paste(im, (x, y))

                                # ========== 使用 spritePathPoints 精確貼上（透明修正版） ==========
                                if hasattr(spriteHandler, 'spritePathPoints') and spriteHandler.spritePathPoints:
                                    points_str = spriteHandler.spritePathPoints[i]
                                    
                                    # 1. 解析座標列表
                                    import ast
                                    try:
                                        points = ast.literal_eval(points_str)
                                    except:
                                        import json
                                        points = json.loads(points_str)
                                    
                                    # print(f"解析點數: {len(points)} 個")
                                    
                                    # 2. 取得精靈尺寸
                                    sprite_w, sprite_h = im.size
                                    # print(f"精靈尺寸: {sprite_w}x{sprite_h}")
                                    
                                    # 3. 計算邊界
                                    if not points:
                                        # 點列表為空 → 退回傳統貼圖方式
                                        spriteHandler.outputLog.appendPlainText(f"(Fallback) Empty points for {spriteHandler.spriteIDs[i]}")
                                        x = spriteHandler.spriteX[i]
                                        y = out.size[1] - spriteHandler.spriteY[i] - im.size[1]
                                        out.paste(im, (x, y))
                                        continue  # 跳過後續遮罩邏輯

                                    rel_xs = [p[0] for p in points]
                                    rel_ys = [p[1] for p in points]

                                    if not rel_xs or not rel_ys:
                                        # 極端情況：points 存在但無 x/y 座標
                                        spriteHandler.outputLog.appendPlainText(f"(Fallback) Invalid points data for {spriteHandler.spriteIDs[i]}")
                                        x = spriteHandler.spriteX[i]
                                        y = out.size[1] - spriteHandler.spriteY[i] - im.size[1]
                                        out.paste(im, (x, y))
                                        continue

                                    min_x, max_x = min(rel_xs), max(rel_xs)
                                    min_y, max_y = min(rel_ys), max(rel_ys)
                                    range_x = max_x - min_x
                                    range_y = max_y - min_y
                                    # print(f"相對範圍: X[{min_x:.3f}~{max_x:.3f}], Y[{min_y:.3f}~{max_y:.3f}]")
                                    
                                    if range_x == 0 or range_y == 0:
                                        print("警告: 範圍為0，使用舊版貼上")
                                        x = spriteHandler.spriteX[i]
                                        y = spriteHandler.spriteY[i]  # 修正為從頂部計算
                                        out.paste(im, (x, y))
                                    else:
                                        # 4. 建立遮罩（L模式，黑=透明）
                                        from PIL import ImageDraw
                                        mask = Image.new('L', (sprite_w, sprite_h), 0)  # 0=透明
                                        draw = ImageDraw.Draw(mask)
                                        
                                        # 5. 逐三角形繪製
                                        for tri_idx in range(0, len(points), 3):
                                            tri_points = points[tri_idx:tri_idx+3]
                                            if len(tri_points) < 3: continue
                                            
                                            # 本地像素座標（Y翻轉）
                                            pixel_points = [
                                                (
                                                    int((rel_x - min_x) / range_x * sprite_w),
                                                    int((max_y - rel_y) / range_y * sprite_h)
                                                )
                                                for rel_x, rel_y in tri_points
                                            ]
                                            draw.polygon(pixel_points, fill=255)  # 255=不透明
                                        
                                        # 6. 確保 im 是 RGBA
                                        if im.mode != 'RGBA':
                                            im = im.convert('RGBA')
                                        
                                        # 7. 貼上位置（修正為從頂部計算）
                                        x = spriteHandler.spriteX[i]
                                        y = out.size[1] - spriteHandler.spriteY[i] - sprite_h  # ✅ 從底部！
                                        
                                        # 8. 邊界檢查
                                        x = max(0, min(x, out.size[0] - sprite_w))
                                        y = max(0, min(y, out.size[1] - sprite_h))
                                        
                                        packing_rotation = spriteHandler.spriteRotate[i]
                                        match packing_rotation:
                                            case SpritePackingRotation.FLIP_HORIZONTAL.value: # 應該是修好了
                                                im = im.transpose(Image.FLIP_TOP_BOTTOM)
                                                mask = mask.transpose(Image.FLIP_LEFT_RIGHT)
                                            case SpritePackingRotation.FLIP_VERTICAL.value: # 修好
                                                im = im.transpose(Image.FLIP_TOP_BOTTOM)
                                                mask = mask.transpose(Image.FLIP_TOP_BOTTOM)
                                            case SpritePackingRotation.ROTATE_180.value: # 修好
                                                im = im.transpose(Image.FLIP_TOP_BOTTOM)
                                                mask = mask.transpose(Image.FLIP_LEFT_RIGHT)
                                                mask = mask.transpose(Image.FLIP_TOP_BOTTOM)
                                            case SpritePackingRotation.NONE.value: # 修好
                                                im = im.transpose(Image.FLIP_TOP_BOTTOM)

                                            # ROTATE_90 沒遇到
                                    
                                        # 上下翻轉
                                        im = im.transpose(Image.FLIP_TOP_BOTTOM) 
                                        # 9. ✅ 正確貼上：用 mask 而非 im！
                                        out.paste(im, (x, y), mask)
                                        
                                        # 10. 除錯：顯示遮罩像素數
                                        white_pixels = sum(1 for pixel in mask.getdata() if pixel > 0)
                                        # print(f"遮罩有效像素: {white_pixels}/{sprite_w*sprite_h} ({white_pixels/(sprite_w*sprite_h)*100:.1f}%)")
                                        
                                        # 11. 日誌
                                        # spriteHandler.outputLog.appendPlainText(
                                        #     f"✓ 透明遮罩: {spriteHandler.spriteIDs[i]} "
                                        #     f"[{x},{y}] ({white_pixels}像素)"
                                        # )
                                        
                                        
                                else:  # 舊版
                                    x = spriteHandler.spriteX[i]
                                    y = spriteHandler.spriteY[i]  # 修正為從頂部計算
                                    out.paste(im, (x, y))
                                
                    try:
                        out.save(outputDir + "/" + spriteCollectionList[j] + ".png")
                    except OSError:
                        return False
    
    
    
    @staticmethod
    def attemptToLoadImageFile(path):
        if path == "":
            return { "img": None, "err": "FileNotFound" }
        try:
            img = Image.open(path)
            return { "img": img, "err": "" }
        except FileNotFoundError as ex:
            return { "img": None, "err": "FileNotFound" }
        except:
            return { "img": None, "err": "Unknown" }
    
    
    
    @staticmethod
    def getBaseAtlasPath(collection):
        if collection in spriteHandler.spriteAtlases:
            return spriteHandler.spriteAtlases[collection]
        return ""
    
    
    
    def getCachedAtlasImg(collection, flipped):
        cache_name = collection
        if flipped:
            cache_name = cache_name + "__Flipped"
        
        if cache_name in spriteHandler.atlasImgCache:
            return spriteHandler.atlasImgCache[cache_name]
        atlas_path = spriteHandler.getBaseAtlasPath(collection)
        atlas_load = spriteHandler.attemptToLoadImageFile(atlas_path)
        atlas_img = atlas_load["img"]
        
        if flipped and not (atlas_img is None):
            atlas_img = atlas_img.transpose(Image.FLIP_LEFT_RIGHT)
            atlas_img = atlas_img.rotate(-90, expand=True)
        
        spriteHandler.atlasImgCache[cache_name] = atlas_img
        return atlas_img
    
    
    
    @staticmethod
    def loadDuplicates(animation):
        spriteHandler.duplicatesHashList = []
        spriteHandler.duplicatesList = []
        
        # Old, Hard Coded Duplicate List
        
        #filePath = os.path.abspath(
        #    os.path.join(os.path.dirname(__file__), "resources/duplicatedata.json")
        #)
        #duplicatesDict = json.load(open(filePath, "r"))
        
        # New, Dynamically Generated Duplicate List
        duplicatesDict = spriteHandler.duplicatesCache
        
        keyList = list(duplicatesDict.keys())
        valueList = list(duplicatesDict.values())
        for path in spriteHandler.spritePath:
            filteredValues = [x for x in valueList if path in x]
            # print(filteredValues)
            if len(filteredValues) != 0:
                groupOfDuplicates = filteredValues[0]
                loadedDuplicates = [
                    x for x in groupOfDuplicates if x in spriteHandler.spritePath
                ]
                # #print(groupOfDuplicates)
                # #print(loadedDuplicates)
                if not loadedDuplicates in spriteHandler.duplicatesList:
                    if len(loadedDuplicates) > 1:
                        if animation in path or animation == "":
                            spriteHandler.duplicatesHashList.append(
                                keyList[valueList.index(groupOfDuplicates)]
                            )
                            spriteHandler.duplicatesList.append(loadedDuplicates)
        # print(spriteHandler.duplicatesList)



    @staticmethod
    def copyMain(main):
        # print(main)
        # print(spriteHandler.duplicatesList)
        groupOfDuplicates = copy.deepcopy(
            [x for x in spriteHandler.duplicatesList if main in x][0]
        )
        # print(groupOfDuplicates)
        groupOfDuplicates.remove(main)
        mainIndex = spriteHandler.spritePath.index(main)
        
        # Abort when main copy is missing
        main_img_path = spriteHandler.basepath + "/" + main
        main_img_path = spriteHandler.attemptToLoadImageFile(main_img_path)
        if main_img_path["err"] != "":
            return
        main_img = main_img_path["img"]
        
        main_img = main_img.crop(
            (
                spriteHandler.spriteXR[mainIndex],
                main_img.size[1]
                - spriteHandler.spriteYR[mainIndex]
                - spriteHandler.spriteH[mainIndex],
                spriteHandler.spriteXR[mainIndex] + spriteHandler.spriteW[mainIndex],
                main_img.size[1] - spriteHandler.spriteYR[mainIndex],
            )
        )
        for image in groupOfDuplicates:
            duplicateIndex = spriteHandler.spritePath.index(image)
            
            # Skip missing files
            dup_img_path = spriteHandler.basepath + "/" + image
            dup_img_load = spriteHandler.attemptToLoadImageFile(dup_img_path)
            if dup_img_load["err"] != "":
                continue
            dup_img = dup_img_load["img"]
            
            dup_img.paste(
                main_img,
                (
                    spriteHandler.spriteXR[duplicateIndex],
                    dup_img.size[1]
                    - spriteHandler.spriteYR[duplicateIndex]
                    - spriteHandler.spriteH[duplicateIndex],
                ),
            )
            dup_img.save(dup_img_path)



    @staticmethod
    def sortByHash(index, vanillaHash):
        # print(spriteHandler.duplicatesList[index])

        def sortFunc(file):
            if file in spriteHandler.spritePath:
                i = spriteHandler.spritePath.index(file)
                img_path = spriteHandler.basepath + "/" + spriteHandler.spritePath[i]
                img_load = spriteHandler.attemptToLoadImageFile(img_path)
                if img_load["err"] != "":
                    return 3
                im = img_load["img"]
                im = im.crop(
                    (
                        spriteHandler.spriteXR[i],
                        im.size[1]
                        - spriteHandler.spriteYR[i]
                        - spriteHandler.spriteH[i],
                        spriteHandler.spriteXR[i] + spriteHandler.spriteW[i],
                        im.size[1] - spriteHandler.spriteYR[i],
                    )
                )
                imData = im.getdata()
                newHash = hash(tuple(map(tuple, imData)))
                # print(file)
                # print(type(newHash))
                # print(type(vanillaHash))
                if str(newHash) == vanillaHash:
                    # print("equal")
                    return 1
                else:
                    # print("not equal")
                    return 0
            else:
                return 2

        # print("sorted list")
        # print(sorted(spriteHandler.duplicatesList[index], key=sortFunc))
        # print("done sort")
        return sorted(spriteHandler.duplicatesList[index], key=sortFunc)



    @staticmethod
    def getVanillaHash(sprite_id):
        if sprite_id in spriteHandler.duplicatesHashCache:
            return spriteHandler.duplicatesHashCache[sprite_id]
        
        collection = spriteHandler.duplicatesData[sprite_id]["collection"]
        atlas_data = spriteHandler.duplicatesData[sprite_id]
        atlas_img = spriteHandler.getCachedAtlasImg(collection, atlas_data["flipped"])
        if atlas_img is None:
            return ""
            
        box_x = atlas_data["x"]
        box_y = atlas_data["y"]
        box_width = atlas_data["width"]
        box_height = atlas_data["height"]
        
        if atlas_data["flipped"]:
            (box_x, box_y) = (box_y, box_x)
            
        box = (
            box_x,
            atlas_img.height - box_y - box_height,
            box_x + box_width,
            atlas_img.height - box_y
        )
            
        croped_img = atlas_img.crop(box)
        img_data = croped_img.getdata()
        vanilla_hash = str(hash(tuple(map(tuple, img_data))))
        spriteHandler.duplicatesHashCache[sprite_id] = vanilla_hash
        
        debug_name = "_".join([
                str(atlas_data["collection"]),
                str(atlas_data["x"]),
                str(atlas_data["y"]),
                str(atlas_data["width"]),
                str(atlas_data["height"])
            ])
        # croped_img.save(spriteHandler.savedOutputFolder + "/debug/" + debug_name + ".png")
        
        return vanilla_hash



    @staticmethod
    def checkCompletion(duplicates, sprite_id, skip_vanilla = False):
        custom_hash = ""
        collection = ""
        for sprite in duplicates:
            i = spriteHandler.spritePath.index(sprite)
            
            img_path = spriteHandler.basepath + "/" + spriteHandler.spritePath[i]
            img_load = spriteHandler.attemptToLoadImageFile(img_path)
            if img_load["err"] != "":
                continue
            im = img_load["img"]
            
            im = im.crop(
                (
                    spriteHandler.spriteXR[i],
                    im.size[1] - spriteHandler.spriteYR[i] - spriteHandler.spriteH[i],
                    spriteHandler.spriteXR[i] + spriteHandler.spriteW[i],
                    im.size[1] - spriteHandler.spriteYR[i],
                )
            )
            imData = im.getdata()
            newHash = hash(tuple(map(tuple, imData)))
            # print(sprite)
            # print(type(newHash))
            # print(type(vanillaHash))
            if custom_hash == "":
                custom_hash = str(newHash)
                collection = spriteHandler.spriteCollection[i]
                atlas_index = i
            elif custom_hash != str(newHash):
                return 0 # Not All Equal
        if not skip_vanilla:
            if collection in spriteHandler.spriteAtlases:
                if custom_hash == spriteHandler.getVanillaHash(sprite_id):
                    return 2 # All Vanilla
        return 1 # All Equal
