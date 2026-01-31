class ErrorException:
    '''
    错误异常日志
    '''
    def __init__(self, filename: str):
        import traceback
        import logging

        logging.basicConfig(
            encodings='utf8',
            filename=filename,
            format='%(asctime)s %(levelname)s \n %(message)s',
            datefmt='%Y-%m-%d %H:%M:%S'
        )

        logging.error(traceback.format_exc())