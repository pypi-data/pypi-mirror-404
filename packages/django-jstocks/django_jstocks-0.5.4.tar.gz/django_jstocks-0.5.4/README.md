Library for Managing Shares Issuance
====================================

Features
--------
* Share registry, ownership information and parties
* Share authorization and allocation to subscribers
* Share transfers
  * Share ownership tracking by sequences
  * Sequence has constant space requirement independent of sequence length
* Double entry accounting system


Install
-------

* pip install django-jshares


About Terminology
-----------------

Issued shares = number of shares of a corporation which have been allocated (allotted) and are subsequently held by shareholders

Issuance = The act of creating new issued shares is called issuance, allocation or allotment. Allotment is simply the creation of shares and their transfer to a subscriber. After allotment, a subscriber becomes a shareholder, though usually that also requires formal entry in the share registry.

Total authorized shares = The number of shares that can be issued. Issued shares are those shares which the board of directors and/or shareholders have agreed to allocate. 

Issued shares are the sum of outstanding shares held by shareholders; and treasury shares are shares which had been issued but have been repurchased by the corporation, and which generally have no voting rights or rights to dividends.

Shares are most commonly issued fully paid, in which case the liability of the shareholders is limited to the amount paid on the shares; but they may also be issued partly paid, with unlimited liability, subject to guarantee, or some other form.

So, as summary, the basic formula:

* Shares authorized = Shares issued + Shares unissued
* Shares issued = Shares outstanding + Treasury shares

(source: https://en.wikipedia.org/wiki/Issued_shares)
