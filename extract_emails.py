import mailbox
import os
import email
from email.header import decode_header
from datetime import datetime
import re

def make_safe_filename(subject):
    """Sanitizes the subject to be used as a filename."""
    keepcharacters = (' ', '.', '_', '-')
    # Strip dots and spaces from ends as Windows doesn't like trailing dots in folders
    return "".join(c for c in subject if c.isalnum() or c in keepcharacters).strip(" ._")

def get_sender_foldername(sender_header):
    """Extracts a safe folder name from the sender header."""
    # Common formats: "Name <email@example.com>" or "email@example.com"
    # We prefer the name if available, otherwise email.
    
    if not sender_header:
        return "Unknown_Sender"
        
    # Try to extract name "Name <...>"
    match = re.match(r'(.*)\s*<.*>', sender_header)
    if match:
        name = match.group(1).strip()
        # Remove quotes if present
        name = name.strip('"').strip("'")
    else:
        # Just use the whole thing (likely just email)
        name = sender_header.strip()
        
    return make_safe_filename(name)[:50].strip() or "Unknown_Sender"

def get_body_and_attachments(message, file_index, output_dir):
    """Extracts body and saves attachments."""
    body = None
    attachments = []
    
    # Attachments go to a central 'attachments' folder in the root output_dir
    # to avoid path length issues and keep structure clean.
    att_dir = os.path.join(output_dir, "attachments", f"{file_index:04d}")
    
    if message.is_multipart():
        for part in message.walk():
            ctype = part.get_content_type()
            cdispo = str(part.get('Content-Disposition'))
            
            # Handle attachments
            if 'attachment' in cdispo or (ctype == 'application/pdf'): 
                if 'attachment' not in cdispo and ctype != 'application/pdf':
                    continue
                    
                filename = part.get_filename()
                if filename:
                    filename = decode_mime_header(filename)
                    safe_fname = make_safe_filename(filename)
                    
                    if not os.path.exists(att_dir):
                        os.makedirs(att_dir)
                        
                    att_path = os.path.join(att_dir, safe_fname)
                    
                    try:
                        with open(att_path, 'wb') as f:
                            f.write(part.get_payload(decode=True))
                        attachments.append(att_path)
                    except Exception as e:
                        print(f"Failed to save attachment {filename}: {e}")

            # Handle Body
            elif ctype == 'text/plain' and 'attachment' not in cdispo:
                try:
                    current_payload = part.get_payload(decode=True).decode('utf-8', errors='ignore')
                    if body is None:
                        body = current_payload
                    else:
                         body += "\n" + current_payload
                except:
                    pass
            elif ctype == 'text/html' and 'attachment' not in cdispo and body is None:
                 try:
                     body = part.get_payload(decode=True).decode('utf-8', errors='ignore')
                 except:
                     pass
    else:
        try:
            body = message.get_payload(decode=True).decode('utf-8', errors='ignore')
        except:
            pass
            
    return body, attachments

def decode_mime_header(header_value):
    if not header_value:
        return ""
    decoded_list = decode_header(header_value)
    header_str = ""
    for token, encoding in decoded_list:
        if isinstance(token, bytes):
            if encoding:
                try:
                    header_str += token.decode(encoding, errors='ignore')
                except LookupError:
                    header_str += token.decode('utf-8', errors='ignore')
            else:
                 header_str += token.decode('utf-8', errors='ignore')
        else:
            header_str += str(token)
    return header_str

def save_email(message, output_dir, file_index):
    try:
        raw_sender = decode_mime_header(message['from']) or "Unknown Sender"
        subject = decode_mime_header(message['subject']) or "No Subject"
        date = message['date']
        
        # Determine sender folder
        sender_folder = get_sender_foldername(raw_sender)
        sender_dir = os.path.join(output_dir, sender_folder)
        
        if not os.path.exists(sender_dir):
            os.makedirs(sender_dir)
            
        safe_subject = make_safe_filename(subject)
        filename = f"{file_index:04d}_{safe_subject[:50]}.txt"
        filepath = os.path.join(sender_dir, filename)
        
        # Pass the sender_dir so attachments are saved inside the sender's folder
        body, attachments = get_body_and_attachments(message, file_index, sender_dir)
        
        with open(filepath, "w", encoding="utf-8") as f:
            f.write(f"Subject: {subject}\n")
            f.write(f"From: {raw_sender}\n")
            f.write(f"Date: {date}\n")
            
            if attachments:
                f.write("Attachments:\n")
                for att in attachments:
                    # Relpath from the EMAIL file to the ATTACHMENT file
                    # Email is in: output_dir/Sender/email.txt
                    # Attachment is in: output_dir/Sender/attachments/id/file.ext
                    # Result should be: attachments/id/file.ext
                    rel_path = os.path.relpath(att, sender_dir)
                    f.write(f"- {rel_path}\n")
            
            f.write("-" * 40 + "\n\n")
            
            if body:
                f.write(body)
            else:
                f.write("[No readable text body found]\n")
                
        return True
    except Exception as e:
        print(f"Error saving email {file_index}: {e}")
        return False

def extract_emails(mbox_path, output_dir, limit=None, keyword=None):
    if not os.path.exists(output_dir):
        os.makedirs(output_dir)
        
    print(f"Opening mbox: {mbox_path}")
    mbox = mailbox.mbox(mbox_path)
    
    count = 0
    extracted = 0
    
    print("Starting extraction...")
    for message in mbox:
        count += 1
        
        if keyword:
            subject = decode_mime_header(message['subject'])
            sender = decode_mime_header(message['from'])
            if keyword.lower() not in subject.lower() and keyword.lower() not in sender.lower():
                continue

        if save_email(message, output_dir, count):
            extracted += 1
            if extracted % 100 == 0:
                print(f"Extracted {extracted} emails...")
        
        if limit and extracted >= limit:
            print(f"Reached limit of {limit} emails.")
            break
            
    print(f"Done. Processed {count} messages. Extracted {extracted} files to '{output_dir}'.")

if __name__ == "__main__":
    import argparse
    
    parser = argparse.ArgumentParser(description="Extract emails from mbox file")
    parser.add_argument("mbox_file", help="Path to .mbox file")
    parser.add_argument("--out", default="output", help="Output directory")
    parser.add_argument("--limit", type=int, help="Max emails to extract")
    parser.add_argument("--keyword", help="Filter by keyword in Subject or From")
    
    args = parser.parse_args()
    
    extract_emails(args.mbox_file, args.out, args.limit, args.keyword)
