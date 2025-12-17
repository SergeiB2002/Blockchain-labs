// SPDX-License-Identifier: MIT
pragma solidity ^0.8.0;

contract SimpleStorage {
    uint256 private storedData;
    
    event ValueChanged(uint256 oldValue, uint256 newValue, address changer);
    
    constructor(uint256 initialValue) {
        storedData = initialValue;
        emit ValueChanged(0, initialValue, msg.sender);
    }
    
    function set(uint256 newValue) public {
        uint256 oldValue = storedData;
        storedData = newValue;
        emit ValueChanged(oldValue, newValue, msg.sender);
    }
    
    function get() public view returns (uint256) {
        return storedData;
    }
}
