import json

def tracker_response(failure_reason: str, warning_msg: str, tracker_id: int, peers: dict) -> str:
    """generate a string response to the peer"""
    response = {
                'failure_reason': failure_reason, 
                'warning_msg': warning_msg, 
                'tracker_id': tracker_id,
                'peers': peers
            }
    str_response = json.dumps(response)
    print(str_response)
    

if __name__ == '__main__':
    s = tracker_response(failure_reason=None, warning_msg=None, tracker_id=1, peers={'peerid': 1, 'ip': '127.0.0.1', 'port': 22256})
    print(s)