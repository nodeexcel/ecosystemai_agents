def summarizing_chat_for_title(text):
    title_summary_prompt = f"""You are a helpful assistant whose job is to give the title of the chat based on the first message by the user which is {text}. Your job is understand the message provide a short tile about it it within 3-7 words.
      Based on the text judge about what the user is asking or telling about deduce a title from it. Remember if title seems to be vulgar or innormal try to put a better variant for it."""
      
    return title_summary_prompt