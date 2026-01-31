import win32com.client
class SpeechRecognition(object):
    def machineReading(self, content):
        dehua = win32com.client.Dispatch('SAPI.SPVOICE')
        dehua.Speak(content)