import os
import sys

CACHE_FILE = "PDF_Summaries.txt"
MODEL = "gemma4:e4b"


def check_model():
    # quick check to make sure the right ollama model is available
    from ollama import list
    response = list()
    installed = {m["model"] for m in response.models}
    print(f"Installed models: {', '.join(sorted(installed))}")
    if MODEL not in installed:
        print(f"Error: Model '{MODEL}' not installed. Run 'ollama pull {MODEL}' first.")
        return False
    print(f"Using model: {MODEL}\n")
    return True


def pdf_to_images(filepath):
    # convert pdf pages to images so we can feed them to the model
    import fitz
    images = []
    doc = fitz.open(filepath)
    for page_num in range(min(2, len(doc))):
        page = doc[page_num]
        # render at decent dpi for readable text
        pix = page.get_pixmap(dpi=150)
        img_data = pix.tobytes("png")
        import base64
        # model wants base64 encoded images
        images.append(base64.b64encode(img_data).decode("utf-8"))
    return images


def get_ollama_response(content, is_image=False):
    # send the content to ollama and get back a summary
    from ollama import chat
    if is_image:
        response = chat(
            model=MODEL,
            messages=[{
                "role": "user",
                "content": "Summarize this document concisely in 1 sentence or less.",
                "images": content
            }]
        )
    else:
        response = chat(
            model=MODEL,
            messages=[{
                "role": "user",
                "content": f"summarize this file concisely in 1 sentence or less:\n{content}"
            }]
        )
    return response.message.content


def process_file(filepath):
    # figure out what kind of file this is and handle it accordingly
    ext = os.path.splitext(filepath)[1].lower()
    if ext in [".txt", ".md", ".py", ".js", ".json", ".html", ".css", ".xml", ".csv", ".log", ".png", ".jpg"]:
        # read text files directly, keep it under 8k chars so model can handle it
        with open(filepath, "r", encoding="utf-8", errors="replace") as f:
            return f.read()[:8000], False
    elif ext == ".pdf":
        # pdfs need to be converted to images first
        try:
            images = pdf_to_images(filepath)
            if images:
                return images, True
        except Exception as e:
            return str(e), False
    return "", False


def load_cache():
    # pull in any existing summaries from previous runs
    cache = {}
    if os.path.exists(CACHE_FILE):
        with open(CACHE_FILE, "r", encoding="utf-8") as f:
            lines = f.readlines()
            i = 0
            while i < len(lines):
                line = lines[i].strip()
                if line.startswith("> "):
                    name = line[2:]
                    if i + 1 < len(lines):
                        summary = lines[i + 1].strip()
                        cache[name] = summary
                        i += 2
                    else:
                        i += 1
                else:
                    i += 1
    return cache


def save_to_cache(filename, summary):
    # append a new summary to the cache file
    with open(CACHE_FILE, "a", encoding="utf-8") as f:
        f.write(f"> {filename}\n   {summary}\n\n")


def save_header(title):
    # write a nice header at the top of the cache file
    with open(CACHE_FILE, "w", encoding="utf-8") as f:
        f.write(f"{'='*60}\n")
        f.write(f"  {title}\n")
        f.write(f"{'='*60}\n\n")


def main():
    # make sure model is good to go
    if not check_model():
        return

    # get the folder path from args or ask the user
    folder = sys.argv[1] if len(sys.argv) > 1 else input("Enter folder path: ").strip().strip('"')
    if not os.path.isdir(folder):
        print(f"Error: {folder} is not a valid directory")
        return

    # load up any cached summaries
    cache = load_cache()

    # what file types do we care about
    extensions = [".pdf", ".txt", ".md", ".png", ".jpg", ".jpeg"]
    files = sorted(f for f in os.listdir(folder)
                   if os.path.isfile(os.path.join(folder, f))
                   and os.path.splitext(f)[1].lower() in extensions)

    # start a new cache file with a header
    save_header(f"PDF Summaries - {os.path.basename(folder)}")

    # go through each file and summarize it
    for filename in files:
        # skip if we already have this one cached
        if filename in cache:
            print(f"\n> {filename}\n{cache[filename]}\n")
            continue

        filepath = os.path.join(folder, filename)
        print(f"\nProcessing: {filename}")
        content, is_image = process_file(filepath)

        # send it to the model and get a summary back
        if is_image:
            summary = get_ollama_response(content, is_image=True)
        elif not content:
            summary = "[Unsupported file type]"
        else:
            summary = get_ollama_response(content, is_image=False)

        print(f"\n> {filename}\n{summary}\n")
        save_to_cache(filename, summary)
        cache[filename] = summary

    print(f"\n{'='*60}")
    print(f"Done! Summaries saved to {CACHE_FILE}")


if __name__ == "__main__":
    main()