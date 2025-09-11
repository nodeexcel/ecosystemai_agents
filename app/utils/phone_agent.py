import json

async def send_initial_conversation_item(openai_ws, prompt):
    """Send initial conversation so AI talks first."""
    initial_conversation_item = {
        "type": "conversation.item.create",
        "item": {
            "type": "message",
            "role": "user",
            "content": [
                {
                    "type": "input_text",
                    "text": (
                        prompt
                    )
                }
            ]
        }
    }
    await openai_ws.send(json.dumps(initial_conversation_item))
    await openai_ws.send(json.dumps({"type": "response.create", "response": {"modalities": ["text", "audio"]}}))

tools = [
      {
        "type": "function",
        "name": "generate_horoscope",
        "description": "add the two numbers",
        "parameters": {
            "type": "object",
          "properties": {
              "number1": {
                  "type": "integer",
                  "description": "first integer value"
              },
              "number2": {
                  "type": "integer",
                  "description": "second integer value"
              }
              },
          "required": ["number1", "number2"]
        }
      }
    ]

async def initialize_session(openai_ws, prompt, voice):
    """Control initial session with OpenAI."""
    session_update = {
        "type": "session.update",
        "session": {
            "turn_detection": {"type": "server_vad",
                                "interrupt_response": False,
                                "create_response": False,},
            "input_audio_format": "g711_ulaw",
            "output_audio_format": "g711_ulaw",
            "voice": "alloy",
            "instructions": prompt,
            "modalities": ["text"],
            "temperature": 0.8,
            "tools": tools,
            "input_audio_transcription": {  
                "model": "whisper-1",
                "language": "en"
            }
        }
    }
    print('Sending session update:', json.dumps(session_update))
    await openai_ws.send(json.dumps(session_update))

    await send_initial_conversation_item(openai_ws, prompt)
