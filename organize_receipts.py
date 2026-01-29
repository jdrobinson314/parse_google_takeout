import os
import shutil
import re

# Configuration
TARGET_DIR = "sorted_emails_output"

CATEGORIES = {
    "Orders": ["order", "receipt", "invoice", "purchase", "payment", "confirmed", "confirmation", "booking", "reserved"],
    "Delivery": ["shipped", "tracking", "delivery", "delivered", "arriving", "scheduled", "shipment", "way"],
    "Promotions": ["sale", "off", "%", "deal", "newsletter", "exclusive", "limited", "save", "offer", "rewards"],
}

def classify_email(filename, content=""):
    """Determines the category based on filename and content."""
    filename_lower = filename.lower()
    content_lower = content.lower() if content else ""
    
    # Check Subject (Filename) first - usually strongest signal
    for cat, keywords in CATEGORIES.items():
        for keyword in keywords:
            if keyword in filename_lower:
                return cat
                
    # Check Content (if we wanted to read files, but filename is faster and often sufficient)
    # We'll stick to filename for speed unless ambiguous? 
    # Let's read the first few lines of content for "Subject:" line just in case filename is truncated/sanitized too much
    # ignoring content for now for speed and simplicity as filenames are "Subject" based.
    
    return "Other"

def get_email_id(filename):
    """Extracts ID from '0001_Subject.txt' -> '0001'"""
    match = re.match(r"(\d+)_", filename)
    if match:
        return match.group(1)
    return None

def organize_files(base_dir):
    if not os.path.exists(base_dir):
        print(f"Directory {base_dir} does not exist.")
        return

    print(f"Scanning {base_dir}...")
    
    # Iterate over Sender directories
    for sender in os.listdir(base_dir):
        sender_path = os.path.join(base_dir, sender)
        if not os.path.isdir(sender_path):
            continue
            
        try:
            print(f"Processing {sender}...")
        except UnicodeEncodeError:
            # Force ASCII to avoid Windows console issues
            print(f"Processing {sender.encode('ascii', 'replace').decode()}...")
        
        # Iterate over files in Sender directory
        files = [f for f in os.listdir(sender_path) if f.endswith(".txt")]
        
        for filename in files:
            file_path = os.path.join(sender_path, filename)
            
            # Classify
            category = classify_email(filename)
            
            # Create Category Directory
            cat_dir = os.path.join(sender_path, category)
            if not os.path.exists(cat_dir):
                os.makedirs(cat_dir)
                
            # Move Text File
            new_file_path = os.path.join(cat_dir, filename)
            try:
                shutil.move(file_path, new_file_path)
            except Exception as e:
                print(f"Error moving {filename}: {e}")
                continue
                
            # Move Attachments if they exist
            # Attachments are in sender_path/attachments/{ID}
            # We want to move to cat_dir/attachments/{ID}
            # This preserves the relative link "attachments/{ID}/file" inside the text file
            
            email_id = get_email_id(filename)
            if email_id:
                old_att_dir = os.path.join(sender_path, "attachments", email_id)
                if os.path.exists(old_att_dir):
                    new_att_parent = os.path.join(cat_dir, "attachments")
                    if not os.path.exists(new_att_parent):
                        os.makedirs(new_att_parent)
                        
                    new_att_dir = os.path.join(new_att_parent, email_id)
                    # using move, but if destination exists (unlikely unless rerun), it might fail
                    try:
                        shutil.move(old_att_dir, new_att_dir)
                    except Exception as e:
                        print(f"Error moving attachments for {filename}: {e}")
                        
    # Access cleanup: Remove empty 'attachments' folders in Sender root?
    # Keeping it simple for now.

    print("Organization complete.")

if __name__ == "__main__":
    organize_files(TARGET_DIR)
