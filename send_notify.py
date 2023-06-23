from twilio.rest import Client


# TWilio API

account_sid = 'AC84b20c240a5fc9b1c1a974c1418b4c52'
auth_token = '1fd4a8c5b4cfb43a30ca02353adb7d3d'
client = Client(account_sid, auth_token)
def send_whatsapp(number, msg):
    message = client.messages.create(
    from_='whatsapp:+14155238886',
    body=msg,
    to=f'whatsapp:+91{number}'
    )
    print(message.sid)
def send_sms(number, msg):
    message = client.messages.create(  
                              #messaging_service_sid='MG8b7942c4f91845611e26b667bfd3ceba', 
                              from_='+17604650320',
                              body=msg,      
                              to=f'+91{number}' 
                          ) 
    print(message.sid)

send_sms(6305461499 ,"It's working")