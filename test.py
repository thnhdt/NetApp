import os
import hashlib
import math

# peers = {
#     'info_hash': 'abc',
#     'peers':
#     {
#         '123': {
#             'ip': 'ip',
#             'port': 'port'
#         },  
#         '456': {
#             'ip': 'ip',
#             'port': 'port'
#         },
#         '789': {
#             'ip': 'ip',
#             'port': 'port'
#         }
#     },
    
# }
# filtered_peers = {peer_id: peer_info for peer_id, peer_info in peers['peers'].items() if peer_id != '789'}

# # Resulting dictionary with peers that are not '789'
# print(filtered_peers)

peer_id = '123'
peer_info = {
    'abc': '1123'
}



test = [{'abc': {
    'socket': 'socket',
    'bitfield': '1111'
}}]
print(test[0].keys())