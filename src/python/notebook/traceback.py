from traceback import format_exception, walk_tb


def get_clean_traceback(e: BaseException, filename: str):
    keep_frames = False
    frame_count = 0
    for frame, _ in walk_tb(e.__traceback__):
        if keep_frames:
            frame_count += 1
        elif frame.f_code.co_filename == filename:
            keep_frames = True
            frame_count += 1
    return "".join(format_exception(type(e), e, e.__traceback__, -frame_count))
