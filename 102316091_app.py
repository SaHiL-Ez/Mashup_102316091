import streamlit as st
import os
import zipfile
import smtplib
from email.mime.multipart import MIMEMultipart
from email.mime.base import MIMEBase
from email import encoders
import importlib.util
import shutil

# Configuration: Set these to your Gmail details to avoid entering them in the UI every time.
# WARNING: Do not share this file publicly if you put your real password here.
FIXED_SENDER_EMAIL = ""      # e.g. "yourname@gmail.com"
FIXED_APP_PASSWORD = ""      # e.g. "xxxx xxxx xxxx xxxx"

# Load YouTube tokens from Streamlit Secrets and set as environment variables
try:
    if hasattr(st, 'secrets'):
        if 'YOUTUBE_PO_TOKEN' in st.secrets:
            os.environ['YOUTUBE_PO_TOKEN'] = st.secrets['YOUTUBE_PO_TOKEN']
            st.sidebar.success("✅ YouTube po_token loaded")
        if 'YOUTUBE_VISITOR_DATA' in st.secrets:
            os.environ['YOUTUBE_VISITOR_DATA'] = st.secrets['YOUTUBE_VISITOR_DATA']
            st.sidebar.success("✅ YouTube visitor_data loaded")
except Exception as e:
    st.sidebar.warning(f"⚠️ YouTube tokens not found in secrets: {e}")

# Import the CLI script dynamically since it starts with a number
spec = importlib.util.spec_from_file_location("mashup_module", "102316091.py")
mashup_module = importlib.util.module_from_spec(spec)
spec.loader.exec_module(mashup_module)

def create_zip(file_path, zip_name):
    with zipfile.ZipFile(zip_name, 'w') as zipf:
        zipf.write(file_path, os.path.basename(file_path))
    return zip_name

def send_email(recipient_email, attachment_path, sender_email, app_password):
    msg = MIMEMultipart()
    msg['From'] = sender_email
    msg['To'] = recipient_email
    msg['Subject'] = "Your Mashup is Ready!"

    body = "Please find the requested mashup attached."
    # msg.attach(MIMEText(body, 'plain')) # MIMEText missing import? No, just attach file is main goal.

    with open(attachment_path, "rb") as attachment:
        part = MIMEBase("application", "octet-stream")
        part.set_payload(attachment.read())
    
    encoders.encode_base64(part)
    part.add_header(
        "Content-Disposition",
        f"attachment; filename= {os.path.basename(attachment_path)}",
    )

    msg.attach(part)

    try:
        server = smtplib.SMTP('smtp.gmail.com', 587)
        server.starttls()
        server.login(sender_email, app_password)
        text = msg.as_string()
        server.sendmail(sender_email, recipient_email, text)
        server.quit()
        return True, "Email sent successfully!"
    except Exception as e:
        return False, str(e)

st.title("Mashup Generator Service")

with st.form("mashup_form"):
    singer_name = st.text_input("Singer Name", "Sharry Mann")
    num_videos = st.number_input("Number of Videos (>10)", min_value=11, value=11, step=1)
    audio_duration = st.number_input("Audio Duration (sec) (>20)", min_value=20, value=20, step=1)
    email_id = st.text_input("Email Id")
    
    st.markdown("### Email Credentials (Optional)")
    
    # Try to load from secrets (Best practice for Streamlit Cloud)
    secrets_sender = ""
    secrets_password = ""
    try:
        secrets_sender = st.secrets.get("EMAIL_SENDER", "")
        secrets_password = st.secrets.get("EMAIL_PASSWORD", "")
    except Exception:
        # Secrets not found (local run without secrets.toml), ignore
        pass
    
    # Logic: Secrets > Hardcoded > Input
    # Only check "Send Email" by default if credentials exist (Secrets or Fixed)
    has_creds = (secrets_sender and secrets_password) or (FIXED_SENDER_EMAIL and FIXED_APP_PASSWORD)
    
    send_email_checkbox = st.checkbox("Send Result via Email?", value=bool(has_creds))
    
    sender_email = ""
    app_password = ""
    
    if send_email_checkbox:
        if secrets_sender and secrets_password:
             sender_email = secrets_sender
             app_password = secrets_password
             st.info("Using credentials from Streamlit Secrets.")
        elif FIXED_SENDER_EMAIL and FIXED_APP_PASSWORD:
             sender_email = FIXED_SENDER_EMAIL
             app_password = FIXED_APP_PASSWORD
             st.info(f"Using configured sender email: {FIXED_SENDER_EMAIL}")
        else:
            sender_email = st.text_input("Sender Email (Gmail)", placeholder="your_email@gmail.com")
            app_password = st.text_input("App Password", type="password", placeholder="xxxx xxxx xxxx xxxx")
    
    submitted = st.form_submit_button("Submit")

if submitted:
    # Validate email only if checkbox is checked
    if send_email_checkbox and (not email_id or not sender_email or not app_password):
        st.error("To send an email, please provide Recipient Email, Sender Email, and App Password.")
    else:
        status_text = st.empty()
        status_text.info("Starting process... Please wait.")
        
        output_file = "mashup_output_web.mp3"
        zip_file = "mashup_output.zip"
        temp_dir = "temp_mashup_web"

        try:
            # 1. Download and Convert
            status_text.info(f"Downloading {num_videos} videos of {singer_name}...")
            mashup_module.download_and_convert(singer_name, num_videos, temp_dir)
            
            # 2. Process
            status_text.info("Processing audio files...")
            mashup_module.process_audios(temp_dir, audio_duration, output_file)
            
            # Check if output file was created
            if not os.path.exists(output_file):
                st.error("Failed to generate audio file. Please check logs for errors (e.g., download issues or processing errors).")
            else:
                # 3. Zip
                status_text.info("Zipping the output...")
                create_zip(output_file, zip_file)
                
                # 4. Email (Optional)
                if send_email_checkbox:
                    status_text.info(f"Sending email to {email_id}...")
                    success, message = send_email(email_id, zip_file, sender_email, app_password)
                    
                    if success:
                        st.success("Done! Email sent successfully.")
                    else:
                        st.error(f"Failed to send email: {message}")
                
                # 5. Download Button (Always)
                st.success("Mashup generated successfully!")
                with open(zip_file, "rb") as fp:
                    btn = st.download_button(
                        label="Download Zip",
                        data=fp,
                        file_name="mashup_output.zip",
                        mime="application/zip"
                    )
                
        except Exception as e:
            st.error(f"An error occurred: {e}")
            
        finally:
            # Cleanup
            mashup_module.clean_up(temp_dir)
            if os.path.exists(output_file):
                os.remove(output_file)
            if os.path.exists(zip_file):
                os.remove(zip_file)
