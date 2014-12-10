#
#  Copyright (C) 2001  Ryan Finne <ryan@finnie.org>
#
#  This program is free software; you can redistribute it and/or modify
#  it under the terms of the GNU General Public License as published by
#  the Free Software Foundation; either version 2 of the License, or
#  (at your option) any later version.
#
#  This program is distributed in the hope that it will be useful,
#  but WITHOUT ANY WARRANTY; without even the implied warranty of
#  MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#  GNU General Public License for more details.
#
#  You should have received a copy of the GNU General Public License
#  along with this program; if not, write to the Free Software
#  Foundation, Inc., 59 Temple Place, Suite 330, Boston, MA  02111-1307  USA
#
def byte2bin(y, p=0):
  res2 = []
  for x in y:
    z = x
    res = []
    x = ord(x)
    while x > 0:
      res.append(x & 1)
      x = x >> 1
    if p > 0:
      res.extend([0] * (p - len(res)))
    res.reverse()
    res2.extend(res)
  return res2

def bin2byte(x):
  i = 0;
  out = ''
  x.reverse()
  b = 1
  ttl = 0
  for y in x:
    i += 1
    ttl += y * b
    b *= 2
    if i == 8:
      i = 0
      out += chr(ttl)
      b = 1
      ttl = 0
  if b > 1:
    out += chr(ttl)
  out = list(out)
  out.reverse()
  out = ''.join(out)
  return out

def bin2dec(x):
  x.reverse()
  b = 1
  ttl = 0
  for y in x:
    ttl += y * b
    b *= 2
  return ttl

def dec2bin(x, p=0):
  res = []
  while x > 0:
    res.append(x & 1)
    x = x >> 1
  if p > 0:
    res.extend([0] * (p - len(res)))
  res.reverse()
  return res

def synchsafe2bin(x):
  out = []
  c = 0
  while len(x) > 0:
    c += 1
    y = x.pop()
    if c == 8:
      c = 0
    else:
      out.append(y)
  out.reverse()
  return out

def bin2synchsafe(x):
  x.reverse()
  out = []
  c = 0
  while len(x) > 0:
    c += 1
    if c == 1:
      out.append(0)
    y = x.pop()
    out.append(y)
    if c == 7:
      c = 0
  return out

