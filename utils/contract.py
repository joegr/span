"""
Solidity contract interface for the NLP Chain
"""

CONTRACT_SOURCE = """
// SPDX-License-Identifier: MIT
pragma solidity ^0.8.0;

contract NLPChain {
    struct DataBlock {
        string data;
        uint256 timestamp;
    }
    
    DataBlock[] private blocks;
    
    function storeData(string memory _data) public {
        blocks.push(DataBlock({
            data: _data,
            timestamp: block.timestamp
        }));
    }
    
    function getData(uint256 _index) public view returns (string memory) {
        require(_index < blocks.length, "Index out of bounds");
        return blocks[_index].data;
    }
    
    function getDataCount() public view returns (uint256) {
        return blocks.length;
    }
}
""" 