"""
Utilities
"""
from django.conf import settings

# https://github.com/OpenDrift/opendrift/blob/master/opendrift/models/OBJECTPROP.DAT
LEEWAY_OBJECT_TYPES = (
    (1, 'Person-in-water (PIW), unknown state (mean values)'),
    (2, '>PIW, vertical PFD type III conscious'),
    (3, '>PIW, sitting, PFD type I or II'),
    (4, '>PIW, survival suit (face up)'),
    (5, '>PIW, scuba suit (face up)'),
    (6, '>PIW, deceased (face down)'),
    (7, 'Life raft, deep ballast (DB) system, general, unknown capacity and loading (mean values)'),
    (8, '>4-14 person capacity, deep ballast system, canopy (average)'),
    (9, '>>4-14 person capacity, deep ballast system, no drogue'),
    (10, '>>>4-14 person capacity, deep ballast system, canopy, no drogue, light loading'),
    (11, '>>>4-14 person capacity, deep ballast system, no drogue, heavy loading'),
    (12, '>>4-14 person capacity, deep ballast system, canopy, with drogue (average)'),
    (13, '>>>4-14 person capacity, deep ballast system, canopy, with drogue, light loading'),
    (14, '>>>4-14 person capacity, deep ballast system, canopy, with drogue, heavy loading'),
    (15, '>15-50 person capacity, deep ballast system, canopy, general (mean values)'),
    (16, '>>15-50 person capacity, deep ballast system, canopy, no drogue, light loading'),
    (17, '>>15-50 person capacity, deep ballast system, canopy, with drogue, heavy loading'),
    (18, 'Deep ballast system, general (mean values), capsized'),
    (19, 'Deep ballast system, general (mean values), swamped'),
    (20, 'Life-raft, shallow ballast (SB) system AND canopy, general (mean values)'),
    (21, '>Life-raft, shallow ballast system, canopy, no drogue'),
    (22, '>Life-raft, shallow ballast system AND canopy, with drogue'),
    (23, 'Life-raft, shallow ballast system AND canopy, capsized'),
    (24, 'Life Raft - Shallow ballast, canopy, Navy Sub Escape (SEIE) 1-man raft, NO drogue'),
    (25, 'Life Raft - Shallow ballast, canopy, Navy Sub Escape (SEIE) 1-man raft, with drogue'),
    (26, 'Life-raft, no ballast (NB) system, general (mean values)'),
    (27, '>Life-raft, no ballast system, no canopy, no drogue'),
    (28, '>Life-raft, no ballast system, no canopy, with drogue'),
    (29, '>Life-raft, no ballast system, with canopy, no drogue'),
    (30, '>Life-raft, no ballast system, with canopy, with drogue'),
    (31, 'Survival Craft - USCG Sea Rescue Kit - 3 ballasted life rafts and 300 meter of line'),
    (32, 'Life-raft, 4-6 person capacity, no ballast, with canopy, no drogue'),
    (33, 'Evacuation slide with life-raft, 46 person capacity'),
    (34, 'Survival Craft - SOLAS Hard Shell Life Capsule, 22 man'),
    (35, 'Survival Craft - Ovatek Hard Shell Life Raft, 4 and 7-man, lightly loaded, no drogue (average)'),
    (36, '>Survival Craft - Ovatek Hard Shell Life Raft, 4 man, lightly loaded, no drogue'),
    (37, '>Survival Craft - Ovatek Hard Shell Life Raft, 7 man, lightly loaded, no drogue'),
    (38, 'Survival Craft - Ovatek Hard Shell Life Raft, 4 and 7-man, fully loaded, drogued (average)'),
    (39, '>Survival Craft - Ovatek Hard Shell Life Raft, 4 man, fully loaded, drogued'),
    (40, '>Survival Craft - Ovatek Hard Shell Life Raft, 7 man, fully loaded, drogued'),
    (41, 'Sea Kayak with person on aft deck'),
    (42, 'Surf board with person'),
    (43, 'Windsurfer with mast and sail in water'),
    (44, 'Skiff - modified-v, cathedral-hull, runabout outboard powerboat'),
    (45, 'Skiff, V-hull'),
    (46, 'Skiffs, swamped and capsized'),
    (47, 'Skiff - v-hull bow to stern (aluminum, Norway)'),
    (48, 'Sport boat, no canvas (*1), modified V-hull'),
    (49, 'Sport fisher, center console (*2), open cockpit'),
    (50, 'Fishing vessel, general (mean values)'),
    (51, 'Fishing vessel, Hawaiian Sampan (*3)'),
    (52, '>Fishing vessel, Japanese side-stern trawler'),
    (53, '>Fishing vessel, Japanese Longliner (*3)'),
    (54, '>Fishing vessel, Korean fishing vessel (*4)'),
    (55, '>Fishing vessel, Gill-netter with rear reel (*3)'),
    (56, 'Coastal freighter. (*5)'),
    (57, 'Sailboat Mono-hull (Average)'),
    (58, '>Sailboat Mono-hull (Dismasted, Average)'),
    (59, '>>Sailboat Mono-hull (Dismasted - rudder amidships)'),
    (60, '>>Sailboat Mono-hull (Dismasted - rudder missing)'),
    (61, '>Sailboat Mono-hull (Bare-masted,  Average)'),
    (62, '>>Sailboat Mono-hull (Bare-masted, rudder amidships)'),
    (63, '>>Sailboat Mono-hull (Bare-masted, rudder hove-to)'),
    (64, 'Sailboat Mono-hull, fin keel, shallow draft (was SAILBOAT-2)'),
    (65, 'Sunfish sailing dingy  -  Bare-masted, rudder missing'),
    (66, 'Fishing vessel debris'),
    (67, 'Self-locating datum marker buoy - no windage'),
    (68, 'Navy Submarine EPIRB (SEPIRB)'),
    (69, 'Bait/wharf box, holds a cubic metre of ice, mean values (*6)'),
    (70, 'Bait/wharf box, holds a cubic metre of ice, lightly loaded'),
    (71, '>Bait/wharf box, holds a cubic metre of ice, full loaded'),
    (72, '55-gallon (220 l) Oil Drum'),
    (73, 'Scaled down (1:3) 40-ft Container (70% submerged)'),
    (74, '20-ft Container (80% submerged)'),
    (75, 'WII L-MK2 mine '),
    (76, 'Immigration vessel, Cuban refugee-raft, no sail (*7)'),
    (77, 'Immigration vessel, Cuban refugee-raft, with sail (*7)')
)

SIMULATION_ARGUMENTS = ["latitude", "longitude", "duration", "radius", "object_type", "start_time"]

def send_result_mail(simulation, message_content_func='result_mail'):
    """
    Send result e-mail with simulation image attached.
    """
    import sys
    import smtplib
    from email.mime.multipart import MIMEMultipart

    msg = MIMEMultipart()
    msg['From'] = settings.MAIL_USER
    msg['To'] = simulation.user.email
    content_func = getattr(sys.modules[__name__], message_content_func)
    msg = content_func(simulation, msg)
    smtp = smtplib.SMTP(settings.MAIL_SMTP, 587)
    smtp.starttls()
    smtp.login(settings.MAIL_USER, settings.MAIL_PASS)
    smtp.sendmail(settings.MAIL_USER, simulation.user.email, msg.as_string())
    smtp.close()

def confirmation_mail(simulation, msg):
    """
    Create confirmation mail
    """
    from email.mime.text import MIMEText
    msg['Subject'] = 'Leeway Drift Simulation Order received'
    text = MIMEText(('Request saved. You will receive an e-mail to {} when the simulation '
                     'is finished. Your request ID is {}.').format(
                         simulation.user.email, simulation.uuid
                     ))
    msg.attach(text)
    return msg

def result_mail(simulation, msg):
    """
    Create mail parts for result mail
    """
    import os
    from pathlib import Path
    from email.mime.text import MIMEText
    from email.mime.image import MIMEImage
    image_path = "{}/{}.png".format(settings.SIMULATION_PATH, simulation.uuid)
    success = False
    if Path(image_path).is_file():
        with open(image_path, 'rb') as image_f:
            img_data = image_f.read()
        success = True
    msg['Subject'] = 'Leeway Drift Simulation Result'
    text = MIMEText(mail_result_text(simulation, success))
    msg.attach(text)
    if success:
        image = MIMEImage(img_data, name=os.path.basename(image_path))
        msg.attach(image)
    return msg

def mail_result_text(simulation, success):
    """
    Create a result mail text
    """
    if success:
        text = "Find the image attached."
    else:
        text = "The simulation failed."
    return (
        "Your request with ID {uuid} has been processed. {text}\n\n"
        "Simulation parameters:\n"
        "- Longitude: {longitude}\n"
        "- Latitude: {latitude}\n"
        "- Radius: {radius}\n"
        "- Start time: {start_time}\n"
        "- Duration: {duration}\n"
        "- Object type: {object_type}\n"
    ).format(
        text=text,
        uuid=simulation.uuid,
        longitude=simulation.longitude,
        latitude=simulation.latitude,
        radius=simulation.radius,
        start_time=simulation.start_time,
        duration=simulation.duration,
        object_type=simulation.object_type
    )

def mail_to_simulation(message):
    """
    Parse content of incoming mail and create a simulation and a response
    """
    from django.contrib.auth.models import User
    from .models import LeewaySimulation
    from .tasks import run_leeway_simulation

    from_addr = message.get('From')
    if "<" in from_addr and ">" in from_addr:
        from_addr = from_addr.split("<")[1].rstrip(">")
    try:
        user = User.objects.get(email=from_addr)
    except User.DoesNotExist:
        return
    arguments_subject = parse_mail_arguments(message.get('Subject'))
    arguments_body = parse_mail_arguments(message.get_payload(), delimiter='\n')
    arguments = {**arguments_subject, **arguments_body, "user":user}
    simulation = LeewaySimulation(**arguments)
    simulation.save()
    run_leeway_simulation.apply_async([simulation.uuid])
    send_result_mail(simulation, 'confirmation_mail')

def parse_mail_arguments(text, delimiter=";"):
    """
    Parse simulation arguments from string
    """
    arguments = {}
    parts = text.split(delimiter)
    for part in [part.strip() for part in parts]:
        if "=" in part:
            key, value = part.split("=")
            if key in SIMULATION_ARGUMENTS:
                if key in ["longitude", "latitude"]:
                    arguments[key.strip()] = normalize_dms2dec(value.strip())
                else:
                    arguments[key.strip()] = value.strip()
    return arguments

def normalize_dms2dec(data):
    """
    If the string contains a DMS coordinate then convert to decimal.
    Decimal values are returned as is.
    """
    if "°" in data:
        return dms2dec(data)
    return data
