from pydantic import BaseModel
from typing import Optional

class ISOTP_PAIR(BaseModel):
    rxid: int
    txid: int
    fd: bool
    brs: bool
    extended: bool
    padding_byte: Optional[int] = None
    support_uds: bool = False
    def __str__(self):
        return f"[rxid: {hex(self.rxid)}, txid: {hex(self.txid)}]" + \
            (" UDS supported" if self.support_uds else "") + \
            (", Extended addressing" if self.extended else "") + \
            (", BRS" if self.brs else "") + \
            (", FD" if self.fd else "") + \
            (f", Padding byte {hex(self.padding_byte)}" if self.padding_byte else "")
    
    def __eq__(self, other):
        return self.rxid == other.rxid \
            and self.txid == other.txid \
            and self.fd == other.fd \
            and self.brs == other.brs \
            and self.extended == other.extended \
            and self.padding_byte == other.padding_byte \
            and self.support_uds == other.support_uds
    
    def __hash__(self):
        return hash((self.rxid, self.txid, self.fd, self.brs, self.extended, self.padding_byte, self.support_uds))