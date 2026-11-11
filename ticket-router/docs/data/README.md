# SAP-support ticket data sourcing (PARKED)

Goal: realistic SAP AMS-style tickets (title, description, module, priority, resolver, resolution notes,
reassignment history) for the off-laptop POC.

- [ ] Search public datasets (Kaggle, academic IT-ticket corpora, SAP Community Q&A as problem text).
- [ ] Check licences before use.
- [ ] Improve `scripts/generate_sample_data.py`: noisier text, vague tickets, reassignments,
      cross-module tickets, T-codes/message numbers, multilingual samples.
- Known limit: synthetic data validates plumbing and UX, not decision quality. Real-data backtest is the real test.
