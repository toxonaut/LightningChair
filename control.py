#!/usr/bin/python3

import threading
import time

import grpc
import os
import rpc_pb2 as ln
import rpc_pb2_grpc as lnrpc
import codecs
import pyqrcode
import RPi.GPIO as GPIO

from guizero import App, Text, TextBox, PushButton, Picture

def generate_bill():
    response = stub.WalletBalance(ln.WalletBalanceRequest())
     #welcome_message.value = response.total_balance
    request = ln.Invoice(memo="Test Memo", value=100)
    response = stub.AddInvoice(request)
    #welcome_message.value = response.payment_request
    big_code = pyqrcode.create(response.payment_request)
    big_code.png('code.png', scale=6, module_color=[0, 0, 0, 128], background=[0xff, 0xff, 0xff])
    my_qr.image="code.png"
    my_qr.visible=True
    myhash = response.r_hash
    my_hashtext.value = codecs.encode(myhash, 'hex').decode('ascii')
    pay_counter.value=1
    pay_counter.repeat(1000, pay_countdown)

def relay_on():
    GPIO.setmode(GPIO.BOARD)
    GPIO.setup(pin, GPIO.OUT)
    GPIO.output(pin, GPIO.HIGH)

def relay_off():
    GPIO.output(pin, GPIO.LOW)
    GPIO.cleanup()
    
def pay_countdown():
    pay_counter.value = int(pay_counter.value) + 1
    invoice = stub.LookupInvoice(ln.PaymentHash(r_hash_str=my_hashtext.value))
    if invoice.settled:
        pay_counter.cancel(pay_countdown)
        pay_counter.after(10,paid)
    if int(pay_counter.value) > 3000:
        pay_counter.value = 1
        pay_counter.cancel(pay_countdown)
        pay_counter.after(10,generate_bill)
        
def paid():
    pay_counter.visible = False
    my_qr.image="paid1.jpg"
    my_qr.visible=True
    pay_counter.after(2000,start_use)
        
def start_use():
    use_counter.value=20
    use_counter.visible=True
    my_qr.visible = False
    relay_on()
    welcome_message.value = "Use for this amount of time:"
    use_counter.repeat(1000, use_countdown)
    
def use_countdown():
    use_counter.value = int(use_counter.value) - 1
    if int(use_counter.value) <1:
        use_counter.cancel(use_countdown)
        use_counter.visible = False
        welcome_message.value = "Pay to use"
        relay_off()
        use_counter.after(10,generate_bill)
        
app = App(bg="#13084c", title="Lightning Chair", width=500, height=500)
welcome_message = Text(app, text="Pay to use", size=20, font="Times New Roman", color="blue")
pay_counter =Text(app, text="1", size=10, font="Times New Roman", color="blue", visible=False )
use_counter =Text(app, text="1", size=30, font="Times New Roman", color="blue", visible=False)
my_qr = Picture(app, image="waiting.jpg", width=250,height=250, visible=False)
my_hashtext = Text(app, text="hash", size=10, font="Times New Roman", color="blue", visible=False)
with open(os.path.expanduser('~/MyPython/lnd/admin.macaroon'), 'rb') as f:
    macaroon_bytes = f.read()
    macaroon = codecs.encode(macaroon_bytes, 'hex')
pin=40   
def metadata_callback(context, callback):
    callback([('macaroon', macaroon)], None)
    
os.environ["GRPC_SSL_CIPHER_SUITES"] = 'HIGH+ECDSA'

cert = open(os.path.expanduser('~/MyPython/lnd/tls.cert'), 'rb').read()
cert_creds = grpc.ssl_channel_credentials(cert)
auth_creds = grpc.metadata_call_credentials(metadata_callback)
combined_creds = grpc.composite_channel_credentials(cert_creds, auth_creds)

channel = grpc.secure_channel('<Your IP address>:<port>', combined_creds)

stub = lnrpc.LightningStub(channel)
generate_bill()
app.tk.attributes("-fullscreen",True)
app.display()

