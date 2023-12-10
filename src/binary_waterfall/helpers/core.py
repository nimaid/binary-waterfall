from PIL import Image


def get_size_for_fit_frame(content_size, frame_size):
    content_width, content_height = content_size
    frame_width, frame_height = frame_size

    # First, figure out which dim is limiting
    aspect_ratio = content_width / content_height
    height_if_limit_width = round(frame_width / aspect_ratio)
    width_if_limit_height = round(frame_height * aspect_ratio)
    if height_if_limit_width > frame_height:
        limit_width = False
    else:
        limit_width = True

    # Now, compute the new content size
    if limit_width:
        fit_width = frame_width
        fit_height = height_if_limit_width
    else:
        fit_width = width_if_limit_height
        fit_height = frame_height

    fit_size = (fit_width, fit_height)

    result = {
        "size": fit_size,
        "limit_width": limit_width
    }

    return result


def fit_to_frame(
        image,
        frame_size,
        scaling=Image.NEAREST,
        transparent=False
):
    # Get new content size
    fit_settings = get_size_for_fit_frame(
        content_size=image.size,
        frame_size=frame_size
    )
    content_size = fit_settings["size"]

    content_width, content_height = content_size
    frame_width, frame_height = frame_size

    # Actually scale the content
    resized_content = image.resize(content_size, scaling)

    # Make a black image
    if transparent:
        resized = Image.new(
            mode="RGBA",
            size=frame_size,
            color=(0, 0, 0, 0)
        )
    else:
        resized = Image.new(
            mode="RGBA",
            size=frame_size,
            color=(0, 0, 0, 255)
        )

    # Paste the content onto the background
    if fit_settings["limit_width"]:
        paste_x = 0
        paste_y = round((frame_height - content_height) / 2)
    else:
        paste_x = round((frame_width - content_width) / 2)
        paste_y = 0
    resized.paste(resized_content, (paste_x, paste_y), resized_content)

    return resized
