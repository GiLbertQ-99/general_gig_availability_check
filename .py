from googleapiclient.discovery import build
from google.oauth2.credentials import Credentials
from base64 import urlsafe_b64decode
from bs4 import BeautifulSoup
from selenium import webdriver
from selenium.webdriver.common.by import By
import time
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart

# Authenticate Gmail API
def get_gmail_service():
    # Access credentials.json and authenticate
    creds = Credentials.from_authorized_user_file('credentials.json', ['https://www.googleapis.com/auth/gmail.modify'])
    service = build('gmail', 'v1', credentials=creds)
    return service

# Search for Craigslist alerts in Gmail
def search_craigslist_alerts(service):
    query = 'label:"General Gig Availability Check" is:unread'  # Search within your specific label for unread messages
    results = service.users().messages().list(userId='me', q=query).execute()
    messages = results.get('messages', [])
    return messages  # List of unread emails within the label

# Extract the posting URL and title from the email content
def get_post_url_and_title(service, message_id):
    try:
        # Retrieve email content
        message = service.users().messages().get(userId='me', id=message_id, format='full').execute()
        payload = message['payload']
        for part in payload.get('parts', []):
            if part['mimeType'] == 'text/html':
                email_body = urlsafe_b64decode(part['body']['data']).decode('utf-8')
                soup = BeautifulSoup(email_body, 'html.parser')
                
                # Find the first clickable link
                first_link = soup.find('a')  # Get the very first <a> tag
                if first_link and 'href' in first_link.attrs:
                    post_url = first_link['href']  # Extract the URL
                    post_title = first_link.text.strip()  # Extract the dynamic title (text content of the <a> tag)
                    return post_url, post_title
        
        raise ValueError("No clickable link found in the email.")
    except Exception as e:
        print(f"Error fetching post URL and title for message ID {message_id}: {e}")
        return None, None  # Return None for both if an error occurs

# Extract the randomized email address using Selenium
def get_randomized_email(post_url):
    try:
        driver = webdriver.Chrome()  # Ensure you have ChromeDriver installed
        driver.get(post_url)

        # Find and click the "Reply" button
        try:
            reply_button = driver.find_element(By.CLASS_NAME, 'reply-button')  # Adjust selector as needed
            reply_button.click()
            time.sleep(2)  # Wait for email to load
        except Exception as e:
            raise RuntimeError(f"Failed to find or click the reply button: {e}")

        # Extract the email address
        try:
            email_element = driver.find_element(By.XPATH, "//a[contains(@href, 'mailto:')]")
            randomized_email = email_element.get_attribute("href").replace("mailto:", "")
        except Exception as e:
            raise RuntimeError(f"Failed to extract the randomized email: {e}")

        driver.quit()
        return randomized_email
    except Exception as e:
        print(f"Error processing post URL {post_url}: {e}")
        driver.quit()
        return None

# Send a reply email
def send_reply_email(to_email, subject, body=[]):
    try:
        sender_email = "your_email@example.com"  # Replace with your actual sender email
        password = "your_password"  # Replace with your email password or app-specific password

        msg = MIMEMultipart()
        msg['From'] = sender_email
        msg['To'] = to_email
        msg['Subject'] = subject
        msg.attach(MIMEText(body, 'plain'))

        # Send the email
        try:
            with smtplib.SMTP_SSL('smtp.gmail.com', 465) as server:
                server.login(sender_email, password)
                server.send_message(msg)
            print(f"Email sent successfully to {to_email}")
        except Exception as e:
            raise RuntimeError(f"Error sending email to {to_email}: {e}")

    except Exception as e:
        print(f"Failed to send email to {to_email}: {e}")

# Main function
def main():
    service = get_gmail_service()

    # Step 1: Search for unread Craigslist emails
    messages = search_craigslist_alerts(service)
    if not messages:
        print("No unread Craigslist alerts found.")
        return

    # Step 2: Process each email
    for message in messages:
        message_id = message['id']
        post_url, post_title = get_post_url_and_title(service, message_id)
        if not post_url or not post_title:
            continue
        print(f"Craigslist Post URL: {post_url}")
        print(f"Craigslist Post Title: {post_title}")

        # Step 3: Extract the randomized email address
        randomized_email = get_randomized_email(post_url)
        if not randomized_email:
            continue
        print(f"Randomized Email: {randomized_email}")

        # Step 4: Send a reply
        body = f"""
        Hello,

        I'm reaching out regarding your listing: {post_title}.
        Do you still need someone ?
        """
        subject = f"📍Re: {post_title}"  # Update this dynamically as needed
        send_reply_email(randomized_email, subject, body)

if __name__ == "__main__":
    main()
