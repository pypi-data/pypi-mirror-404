def _varint(value: int) -> bytes:
    """Encode an integer as a varint."""
    out = []
    while True:
        towrite = value & 0x7F
        value >>= 7
        if value:
            out.append(towrite | 0x80)
        else:
            out.append(towrite)
            break
    return bytes(out)

def encode_set_session_options(options: dict) -> bytes:
    """
    Manual protobuf encoding for FlightSQL SetSessionOptionsRequest.
    
    Proto definition:
    message SetSessionOptionsRequest {
      map<string, SessionOptionValue> session_options = 1;
    }
    
    message SessionOptionValue {
      oneof option_value {
        string string_value = 1;
        bool bool_value = 2;
        int64 int64_value = 3;
        double double_value = 4;
        repeated string string_list_value = 5;
      }
    }
    
    Map entries are encoded as repeated messages:
    message Entry {
      string key = 1;
      SessionOptionValue value = 2;
    }
    """
    output = bytearray()
    for key, value in options.items():
        # Encode Entry
        entry_data = bytearray()
        
        # Key (field 1, string) -> tag (1 << 3) | 2 (LEN) = 0x0A
        k_bytes = key.encode('utf-8')
        entry_data.append(0x0A)
        entry_data.extend(_varint(len(k_bytes)))
        entry_data.extend(k_bytes)
        
        # Value (field 2, SessionOptionValue message) -> tag (2 << 3) | 2 (LEN) = 0x12
        # SessionOptionValue containing string_value (field 1)
        val_msg = bytearray()
        
        # string_value (field 1, string) -> tag (1 << 3) | 2 (LEN) = 0x0A
        v_bytes = str(value).encode('utf-8')
        val_msg.append(0x0A)
        val_msg.extend(_varint(len(v_bytes)))
        val_msg.extend(v_bytes)
        
        # Add val_msg as field 2 of Entry
        entry_data.append(0x12)
        entry_data.extend(_varint(len(val_msg)))
        entry_data.extend(val_msg)
        
        # Add Entry to output (field 1, message) -> tag (1 << 3) | 2 (LEN) = 0x0A
        output.append(0x0A)
        output.extend(_varint(len(entry_data)))
        output.extend(entry_data)
        
    return bytes(output)
