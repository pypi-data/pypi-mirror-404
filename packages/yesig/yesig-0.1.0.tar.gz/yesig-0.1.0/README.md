~YESIG~

Yes a simple and efficient python interface for the signal-cli rest api.

Supports jsonrpc mode if websockets are installed.

Installation:

    python -m pip install yesig

Features:
    * Receive messages via GET or JRPC-websocket. 
    * Download Attachments
    * Send messages with attachments or previews
    * More coming as needed :P


Getting new messages with get request:
        
        receiver = RestReceiver(port=1312, attachment_folder=~/signal_attachments)
        msgs = receiver.receive()

Download an Attachment with the receiver:
        
        fpath = receiver.download(THISISMYATTACHMENTID)

Sending messages with Transmitter:
        
        transmitter = Transmitter()
        transmitter.send("Hello world", attachments=["funny_duck.jpg"])
        preview=Preview(url="https://wiki.archlinux.org",title="I use", description="Arch btw", filepath="/path/to/funny_duck.jpg")
        transmitter.send("Did you know" preview=preview)

Receiving messages via websocket:
    
        await receive_from_socket(queue= q) 