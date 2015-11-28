# -*- coding: utf-8 -*-
##############################################################################
#
#    OpenERP, Open Source Management Solution
#    Copyright (c) 2009 Albert Cervera i Areny - NaN  (http://www.nan-tic.com)
#	 All Rights Reserved.
#    Copyright (c) 2010-Today Elico Corp. All Rights Reserved.
#    Author: Andy Lu <andy.lu@elico-corp.com>
#
#    This program is free software: you can redistribute it and/or modify
#    it under the terms of the GNU Affero General Public License as
#    published by the Free Software Foundation, either version 3 of the
#    License, or (at your option) any later version.
#
#    This program is distributed in the hope that it will be useful,
#    but WITHOUT ANY WARRANTY; without even the implied warranty of
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#    GNU Affero General Public License for more details.
#
#    You should have received a copy of the GNU Affero General Public License
#    along with this program.  If not, see <http://www.gnu.org/licenses/>.
#
##############################################################################
{
	"name" : "Manufacturing Order Splitting Wizard",
	"version" : "0.1",
	"description" : """This module adds a new wizard that allows splitting a production order into two.
	Based on the original module Developed by NaN-tic for Trod y Avia, S.L.

	We, Elico corp fixed the bugs and modify the workflow of Manufacturing Order.
	Support:
	-- R/M assigned, can start Manufacturing Order
	-- Modifyt the QTY of R/M in the picking, then synchronize the QTY when Start Order.
	-- Create a picking for produce product, link to the exist stock move.
	-- When you produce the order, the picking move of produce product to be Available ,not Done.
	-- When you finish the picking, then close the Manufacturing order automatically.   
	Andy Lu 2012-09-10
	""",
	"author" : "Elico Corp",
	"website" : "http://www.openerp.net.cn",
	"depends" : [ 
		'mrp', 'procurement'
	],
	"category" : "Manufacturing",
	"init_xml" : [],
	"demo_xml" : [],
	"update_xml" : [ 
		'wizard/mro_mo_split_view.xml',
		'mrp_view.xml'
	],
	"active": False,
	"installable": True
}
