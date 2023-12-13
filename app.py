import time
from openai import OpenAI
import openai
import streamlit as st
import os
import PyPDF2 as pypdf2
from dotenv import load_dotenv

load_dotenv()

print("Starting {0} app........".format(os.getenv("APP1_NAME")))
# print(os.getenv('OPENAI_API_KEY'))
OpenAI.api_key = os.getenv("OPENAI_API_KEY")

client = OpenAI()


def pdf_txt_extract(file):
    pdf = pypdf2.PdfReader(file)
    # print(len(pdf.pages))
    # print(pdf.pages[0].extract_text())
    text_obj = {}
    txt = []
    for page_num in range(len(pdf.pages)):
        page_object = pdf.pages[page_num]
        txt.append(page_object.extract_text())

    text_obj["text"] = txt
    text_obj["pages"] = len(pdf.pages)
    text_obj["title"] = pdf.metadata.title
    text_obj["subject"] = pdf.metadata.subject
    text_obj["bytesizeinmemory"] = pdf.metadata.__sizeof__()
    text_obj["authors"] = pdf.metadata.author
    text_obj["creators"] = pdf.metadata.creator

    return text_obj


def summ_text(txt, max_tokens=150, temp=0.7, p=1, n=1):
    response = None
    while response is None:
        try:
            response = client.chat.completions.create(
                model="gpt-3.5-turbo",
                messages=[
                    {
                        "role": "system",
                        "content": "Summarize content you are provided with.",
                    },
                    {"role": "user", "content": txt},
                ],
                temperature=temp,
                max_tokens=max_tokens,
                top_p=p,
                n=n,
            )
        except Exception as e:
            st.warning(f"OpenAI Rate limit exceeded. Waiting for 60 seconds. Error: {e}")
            time.sleep(60)
    # print(response.choices[0].message.content)
    return response.choices[0].message.content


def chunks(text, max_tokens=4096):
    # print(len(text), type(text), max_tokens)
    chunks = []
    for j in range(len(text)):
        # print(len(text[j]), type(text[j]))
        chunk = [text[j][i : i + max_tokens] for i in range(0, len(text[j]), max_tokens)]
        chunks += chunk
    # print(len(chunks), type(chunks), type(chunks[0]))
    return chunks


def ui_app():
    # Stramlit Basic Page UI
    st.set_page_config(page_title=os.getenv("APP1_NAME"))
    st.title(f"{os.getenv('APP1_NAME')} App")
    st.caption("Powered by OpenAI & Streamlit")
    st.caption("Created by Abhishek Dey")

    # Capture the Input PDF File
    file = st.file_uploader(label="Upload Your PDF Here", type=["pdf"], accept_multiple_files=False)

    # Variable Slidera
    max_tk_val = st.slider("Select Max. Output Token :", min_value=10, max_value=200, value=100)
    temp_val = st.slider("Select Temperature :", min_value=0.1, max_value=2.0, value=0.7)
    top_p_val = st.slider("Select Top P :", min_value=1, max_value=3, value=1)
    n_val = st.slider("Select N :", min_value=1, max_value=3, value=1)

    # Onclick the Summarize Button
    if st.button(label="Summarize"):

        # checks whether the file is available
        if file is not None:
            # Load Spinner
            with st.spinner(text="Generating Summary..."):
                # capture all the variables value
                p_max_tk = max_tk_val
                p_temp = temp_val
                p_top_p = top_p_val
                p_n = n_val

                # Text Extract from File => Dictionary Object
                text = pdf_txt_extract(file)

                # Display the extracted Details in the PDF file
                for key, val in text.items():
                    if key != "text":
                        st.write(key.capitalize(), ":", val)

                # Break into Chuncks
                text_chunks = chunks(text=text["text"], max_tokens=4000)

                # Display Summary Chunck
                st.subheader("Summary: \n")

                for i, t_chunk in enumerate(text_chunks):
                    # Generate summary
                    summ_txt_val = summ_text(txt=t_chunk, temp=p_temp, max_tokens=p_max_tk, p=p_top_p, n=p_n)

                    # Print Summary of the Chunk
                    st.caption(summ_txt_val + "\n")

                    # Waiting for the next chunk to mitigate Open AI rate limit
                    if (((i+1) < len(text_chunks))):
                        time.sleep(30)
                    else:
                        time.sleep(15)

            # print("Completed All Chuncks")

        else:
            st.warning("Please Upload a PDF File")


if __name__ == "__main__":
    try:
        ui_app()
    except Exception as e:
        st.error(body=e.__str__(), icon="🚨")
