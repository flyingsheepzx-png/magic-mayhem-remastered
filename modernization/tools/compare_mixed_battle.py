"""Generate an unshrunk battle size comparison from two hash-verified runs."""
from pathlib import Path
from PIL import Image, ImageDraw, ImageFont

ROOT = Path(__file__).resolve().parents[2]
OLD = ROOT / "modernization/logs/wide169/1790565342027385400/test2.png"
NEW = ROOT / "modernization/logs/wide169/1790581996272622500/test2-native-probe.png"
OUT = ROOT / "modernization/assets/hd/native-ui-2k-probe/battle-size-compare-5120x1440.png"


def main():
    with Image.open(OLD) as old, Image.open(NEW) as new:
        if old.size != (1280, 720) or new.size != (2560, 1440):
            raise ValueError("Unexpected native source size")
        result = Image.new("RGB", (5120, 1440))
        result.paste(old.convert("RGB").resize((2560, 1440), Image.Resampling.NEAREST), (0, 0))
        result.paste(new.convert("RGB"), (2560, 0))
        draw = ImageDraw.Draw(result)
        font = ImageFont.truetype("C:/Windows/Fonts/msyh.ttc", 28)
        for x, text in ((0, "目标：局内 1280×720 原生 → 2560×1440 输出"),
                        (2560, "已否定：局内 2560×1440 原生")):
            draw.rectangle((x, 0, x + 880, 46), fill=(0, 0, 0))
            draw.text((x + 12, 7), text, font=font, fill=(255, 255, 255))
        result.save(OUT)
        print(f"{OUT} {result.size}")


if __name__ == "__main__":
    main()
