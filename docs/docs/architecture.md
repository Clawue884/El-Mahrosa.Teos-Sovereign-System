# 🧱 System Architecture

```mermaid
flowchart TD
    Citizens --> Wallets --> CivicMixer --> BankChain --> Regulators
    BankChain --> ComplianceAPIs --> Regulators
    SmartContracts --> Interoperability --> MultiChain
```

## Layers
- **Identity** → Digital ID, eWallet
- **Payments** → Civic mixer, Pi Taxi, BankChain
- **Governance** → Civic Ledger, Smart City
- **Interoperability** → Wormhole, Axelar, LayerZero
