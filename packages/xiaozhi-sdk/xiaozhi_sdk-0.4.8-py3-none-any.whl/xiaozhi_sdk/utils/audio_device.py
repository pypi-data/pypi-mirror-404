import sounddevice as sd


def get_audio_device_info():
    audio_device_dict = {}
    for dev in sd.query_devices():
        audio_device_dict[dev["index"]] = {
            "index": dev["index"],
            "name": dev["name"],
            "is_input": dev["max_input_channels"] > 0,
            "is_output": dev["max_output_channels"] > 0,
            "samplerate": int(dev["default_samplerate"]),
        }

    return audio_device_dict


def _get_display_width(text):
    """计算字符串的显示宽度（中文字符占2个宽度）"""
    width = 0
    for char in text:
        # 判断是否为中文字符（包括中文标点）
        if ord(char) > 127:
            width += 2
        else:
            width += 1
    return width


def _truncate_string(text, max_display_width):
    """截断字符串到指定的显示宽度，超出部分用...表示"""
    if _get_display_width(text) <= max_display_width:
        return text

    # 如果显示宽度超过限制，需要截断
    result = ""
    current_width = 0
    ellipsis_width = _get_display_width("...")
    max_width = max_display_width - ellipsis_width

    for char in text:
        char_width = 2 if ord(char) > 127 else 1
        if current_width + char_width > max_width:
            break
        result += char
        current_width += char_width

    return result + "..."


def _pad_string(text, width, align="<"):
    """填充字符串到指定显示宽度"""
    # 先截断，确保不超过宽度
    text = _truncate_string(text, width)
    display_width = _get_display_width(text)
    if display_width >= width:
        return text
    padding = width - display_width
    if align == "<":
        return text + " " * padding
    elif align == ">":
        return " " * padding + text
    else:  # center
        left = padding // 2
        right = padding - left
        return " " * left + text + " " * right


def print_audio_devices():
    """打印所有可用的音频设备列表"""
    devices = sd.query_devices()
    default_input = sd.default.device[0]
    default_output = sd.default.device[1]

    # 分离输入和输出设备
    input_devices = []
    output_devices = []

    for i, device in enumerate(devices):
        is_default_input = i == default_input
        is_default_output = i == default_output

        if device["max_input_channels"] > 0:
            input_devices.append(
                {
                    "id": i,
                    "name": device["name"],
                    "channels": device["max_input_channels"],
                    "samplerate": device["default_samplerate"],
                    "is_default": is_default_input,
                }
            )

        if device["max_output_channels"] > 0:
            output_devices.append(
                {
                    "id": i,
                    "name": device["name"],
                    "channels": device["max_output_channels"],
                    "samplerate": device["default_samplerate"],
                    "is_default": is_default_output,
                }
            )

    # 打印输入设备
    if input_devices:
        print("\n" + "-" * 80)
        print("输入设备 (Input Devices)".center(80))
        print("-" * 80)
        # 使用正确的显示宽度对齐
        header = (
            f"{'ID':<6} {_pad_string('设备名称', 50)} {_pad_string('通道', 8)} {_pad_string('采样率', 10)} {'默认'}"
        )
        print(header)
        print("-" * 80)
        for dev in input_devices:
            default_mark = "✓" if dev["is_default"] else ""
            name_padded = _pad_string(dev["name"], 50)
            channels_padded = _pad_string(str(dev["channels"]), 8)
            samplerate_str = f"{int(dev['samplerate'])}Hz"
            samplerate_padded = _pad_string(samplerate_str, 10)
            print(f"{dev['id']:<6} {name_padded} {channels_padded} {samplerate_padded} {default_mark}")

    # 打印输出设备
    if output_devices:
        print("\n" + "-" * 80)
        print("输出设备 (Output Devices)".center(80))
        print("-" * 80)
        # 使用正确的显示宽度对齐
        header = (
            f"{'ID':<6} {_pad_string('设备名称', 50)} {_pad_string('通道', 8)} {_pad_string('采样率', 10)} {'默认'}"
        )
        print(header)
        print("-" * 80)
        for dev in output_devices:
            default_mark = "✓" if dev["is_default"] else ""
            name_padded = _pad_string(dev["name"], 50)
            channels_padded = _pad_string(str(dev["channels"]), 8)
            samplerate_str = f"{int(dev['samplerate'])}Hz"
            samplerate_padded = _pad_string(samplerate_str, 10)
            print(f"{dev['id']:<6} {name_padded} {channels_padded} {samplerate_padded} {default_mark}")

    print("\n" + "=" * 80 + "\n")
