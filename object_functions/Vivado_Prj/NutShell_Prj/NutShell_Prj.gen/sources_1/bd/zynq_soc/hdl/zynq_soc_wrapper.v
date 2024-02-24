//Copyright 1986-2022 Xilinx, Inc. All Rights Reserved.
//Copyright 2022-2023 Advanced Micro Devices, Inc. All Rights Reserved.
//--------------------------------------------------------------------------------
//Tool Version: Vivado v.2023.2 (lin64) Build 4029153 Fri Oct 13 20:13:54 MDT 2023
//Date        : Tue Feb 20 00:19:09 2024
//Host        : cg1710-pi running 64-bit Ubuntu 22.04.4 LTS
//Command     : generate_target zynq_soc_wrapper.bd
//Design      : zynq_soc_wrapper
//Purpose     : IP block netlist
//--------------------------------------------------------------------------------
`timescale 1 ps / 1 ps

module zynq_soc_wrapper
   (AXI_Corpus_araddr,
    AXI_Corpus_arburst,
    AXI_Corpus_arcache,
    AXI_Corpus_arid,
    AXI_Corpus_arlen,
    AXI_Corpus_arlock,
    AXI_Corpus_arprot,
    AXI_Corpus_arqos,
    AXI_Corpus_arready,
    AXI_Corpus_arsize,
    AXI_Corpus_aruser,
    AXI_Corpus_arvalid,
    AXI_Corpus_awaddr,
    AXI_Corpus_awburst,
    AXI_Corpus_awcache,
    AXI_Corpus_awid,
    AXI_Corpus_awlen,
    AXI_Corpus_awlock,
    AXI_Corpus_awprot,
    AXI_Corpus_awqos,
    AXI_Corpus_awready,
    AXI_Corpus_awsize,
    AXI_Corpus_awuser,
    AXI_Corpus_awvalid,
    AXI_Corpus_bid,
    AXI_Corpus_bready,
    AXI_Corpus_bresp,
    AXI_Corpus_bvalid,
    AXI_Corpus_rdata,
    AXI_Corpus_rid,
    AXI_Corpus_rlast,
    AXI_Corpus_rready,
    AXI_Corpus_rresp,
    AXI_Corpus_rvalid,
    AXI_Corpus_wdata,
    AXI_Corpus_wlast,
    AXI_Corpus_wready,
    AXI_Corpus_wstrb,
    AXI_Corpus_wvalid,
    AXI_DMA_araddr,
    AXI_DMA_arburst,
    AXI_DMA_arcache,
    AXI_DMA_arid,
    AXI_DMA_arlen,
    AXI_DMA_arlock,
    AXI_DMA_arprot,
    AXI_DMA_arqos,
    AXI_DMA_arready,
    AXI_DMA_arregion,
    AXI_DMA_arsize,
    AXI_DMA_arvalid,
    AXI_DMA_awaddr,
    AXI_DMA_awburst,
    AXI_DMA_awcache,
    AXI_DMA_awid,
    AXI_DMA_awlen,
    AXI_DMA_awlock,
    AXI_DMA_awprot,
    AXI_DMA_awqos,
    AXI_DMA_awready,
    AXI_DMA_awregion,
    AXI_DMA_awsize,
    AXI_DMA_awvalid,
    AXI_DMA_bid,
    AXI_DMA_bready,
    AXI_DMA_bresp,
    AXI_DMA_bvalid,
    AXI_DMA_rdata,
    AXI_DMA_rid,
    AXI_DMA_rlast,
    AXI_DMA_rready,
    AXI_DMA_rresp,
    AXI_DMA_rvalid,
    AXI_DMA_wdata,
    AXI_DMA_wlast,
    AXI_DMA_wready,
    AXI_DMA_wstrb,
    AXI_DMA_wvalid,
    AXI_DUT_araddr,
    AXI_DUT_arburst,
    AXI_DUT_arcache,
    AXI_DUT_arid,
    AXI_DUT_arlen,
    AXI_DUT_arlock,
    AXI_DUT_arprot,
    AXI_DUT_arqos,
    AXI_DUT_arready,
    AXI_DUT_arsize,
    AXI_DUT_aruser,
    AXI_DUT_arvalid,
    AXI_DUT_awaddr,
    AXI_DUT_awburst,
    AXI_DUT_awcache,
    AXI_DUT_awid,
    AXI_DUT_awlen,
    AXI_DUT_awlock,
    AXI_DUT_awprot,
    AXI_DUT_awqos,
    AXI_DUT_awready,
    AXI_DUT_awsize,
    AXI_DUT_awuser,
    AXI_DUT_awvalid,
    AXI_DUT_bid,
    AXI_DUT_bready,
    AXI_DUT_bresp,
    AXI_DUT_bvalid,
    AXI_DUT_rdata,
    AXI_DUT_rid,
    AXI_DUT_rlast,
    AXI_DUT_rready,
    AXI_DUT_rresp,
    AXI_DUT_rvalid,
    AXI_DUT_wdata,
    AXI_DUT_wlast,
    AXI_DUT_wready,
    AXI_DUT_wstrb,
    AXI_DUT_wvalid,
    AXI_MEM_araddr,
    AXI_MEM_arburst,
    AXI_MEM_arcache,
    AXI_MEM_arid,
    AXI_MEM_arlen,
    AXI_MEM_arlock,
    AXI_MEM_arprot,
    AXI_MEM_arqos,
    AXI_MEM_arready,
    AXI_MEM_arsize,
    AXI_MEM_aruser,
    AXI_MEM_arvalid,
    AXI_MEM_awaddr,
    AXI_MEM_awburst,
    AXI_MEM_awcache,
    AXI_MEM_awid,
    AXI_MEM_awlen,
    AXI_MEM_awlock,
    AXI_MEM_awprot,
    AXI_MEM_awqos,
    AXI_MEM_awready,
    AXI_MEM_awsize,
    AXI_MEM_awuser,
    AXI_MEM_awvalid,
    AXI_MEM_bid,
    AXI_MEM_bready,
    AXI_MEM_bresp,
    AXI_MEM_bvalid,
    AXI_MEM_rdata,
    AXI_MEM_rid,
    AXI_MEM_rlast,
    AXI_MEM_rready,
    AXI_MEM_rresp,
    AXI_MEM_rvalid,
    AXI_MEM_wdata,
    AXI_MEM_wlast,
    AXI_MEM_wready,
    AXI_MEM_wstrb,
    AXI_MEM_wvalid,
    AXI_MMIO_araddr,
    AXI_MMIO_arburst,
    AXI_MMIO_arcache,
    AXI_MMIO_arid,
    AXI_MMIO_arlen,
    AXI_MMIO_arlock,
    AXI_MMIO_arprot,
    AXI_MMIO_arqos,
    AXI_MMIO_arready,
    AXI_MMIO_arsize,
    AXI_MMIO_arvalid,
    AXI_MMIO_awaddr,
    AXI_MMIO_awburst,
    AXI_MMIO_awcache,
    AXI_MMIO_awid,
    AXI_MMIO_awlen,
    AXI_MMIO_awlock,
    AXI_MMIO_awprot,
    AXI_MMIO_awqos,
    AXI_MMIO_awready,
    AXI_MMIO_awsize,
    AXI_MMIO_awvalid,
    AXI_MMIO_bid,
    AXI_MMIO_bready,
    AXI_MMIO_bresp,
    AXI_MMIO_bvalid,
    AXI_MMIO_rdata,
    AXI_MMIO_rid,
    AXI_MMIO_rlast,
    AXI_MMIO_rready,
    AXI_MMIO_rresp,
    AXI_MMIO_rvalid,
    AXI_MMIO_wdata,
    AXI_MMIO_wlast,
    AXI_MMIO_wready,
    AXI_MMIO_wstrb,
    AXI_MMIO_wvalid,
    CLK_IN_D_clk_n,
    CLK_IN_D_clk_p,
    core_clk,
    corerstn,
    intrs,
    pcie_mgt_rxn,
    pcie_mgt_rxp,
    pcie_mgt_txn,
    pcie_mgt_txp,
    uncore_clk,
    uncorerstn);
  input [48:0]AXI_Corpus_araddr;
  input [1:0]AXI_Corpus_arburst;
  input [3:0]AXI_Corpus_arcache;
  input [5:0]AXI_Corpus_arid;
  input [7:0]AXI_Corpus_arlen;
  input AXI_Corpus_arlock;
  input [2:0]AXI_Corpus_arprot;
  input [3:0]AXI_Corpus_arqos;
  output AXI_Corpus_arready;
  input [2:0]AXI_Corpus_arsize;
  input AXI_Corpus_aruser;
  input AXI_Corpus_arvalid;
  input [48:0]AXI_Corpus_awaddr;
  input [1:0]AXI_Corpus_awburst;
  input [3:0]AXI_Corpus_awcache;
  input [5:0]AXI_Corpus_awid;
  input [7:0]AXI_Corpus_awlen;
  input AXI_Corpus_awlock;
  input [2:0]AXI_Corpus_awprot;
  input [3:0]AXI_Corpus_awqos;
  output AXI_Corpus_awready;
  input [2:0]AXI_Corpus_awsize;
  input AXI_Corpus_awuser;
  input AXI_Corpus_awvalid;
  output [5:0]AXI_Corpus_bid;
  input AXI_Corpus_bready;
  output [1:0]AXI_Corpus_bresp;
  output AXI_Corpus_bvalid;
  output [63:0]AXI_Corpus_rdata;
  output [5:0]AXI_Corpus_rid;
  output AXI_Corpus_rlast;
  input AXI_Corpus_rready;
  output [1:0]AXI_Corpus_rresp;
  output AXI_Corpus_rvalid;
  input [63:0]AXI_Corpus_wdata;
  input AXI_Corpus_wlast;
  output AXI_Corpus_wready;
  input [7:0]AXI_Corpus_wstrb;
  input AXI_Corpus_wvalid;
  output [39:0]AXI_DMA_araddr;
  output [1:0]AXI_DMA_arburst;
  output [3:0]AXI_DMA_arcache;
  output [6:0]AXI_DMA_arid;
  output [7:0]AXI_DMA_arlen;
  output [0:0]AXI_DMA_arlock;
  output [2:0]AXI_DMA_arprot;
  output [3:0]AXI_DMA_arqos;
  input [0:0]AXI_DMA_arready;
  output [3:0]AXI_DMA_arregion;
  output [2:0]AXI_DMA_arsize;
  output [0:0]AXI_DMA_arvalid;
  output [39:0]AXI_DMA_awaddr;
  output [1:0]AXI_DMA_awburst;
  output [3:0]AXI_DMA_awcache;
  output [6:0]AXI_DMA_awid;
  output [7:0]AXI_DMA_awlen;
  output [0:0]AXI_DMA_awlock;
  output [2:0]AXI_DMA_awprot;
  output [3:0]AXI_DMA_awqos;
  input [0:0]AXI_DMA_awready;
  output [3:0]AXI_DMA_awregion;
  output [2:0]AXI_DMA_awsize;
  output [0:0]AXI_DMA_awvalid;
  input [6:0]AXI_DMA_bid;
  output [0:0]AXI_DMA_bready;
  input [1:0]AXI_DMA_bresp;
  input [0:0]AXI_DMA_bvalid;
  input [63:0]AXI_DMA_rdata;
  input [6:0]AXI_DMA_rid;
  input [0:0]AXI_DMA_rlast;
  output [0:0]AXI_DMA_rready;
  input [1:0]AXI_DMA_rresp;
  input [0:0]AXI_DMA_rvalid;
  output [63:0]AXI_DMA_wdata;
  output [0:0]AXI_DMA_wlast;
  input [0:0]AXI_DMA_wready;
  output [7:0]AXI_DMA_wstrb;
  output [0:0]AXI_DMA_wvalid;
  input [39:0]AXI_DUT_araddr;
  input [1:0]AXI_DUT_arburst;
  input [3:0]AXI_DUT_arcache;
  input [3:0]AXI_DUT_arid;
  input [7:0]AXI_DUT_arlen;
  input [0:0]AXI_DUT_arlock;
  input [2:0]AXI_DUT_arprot;
  input [3:0]AXI_DUT_arqos;
  output AXI_DUT_arready;
  input [2:0]AXI_DUT_arsize;
  input [0:0]AXI_DUT_aruser;
  input AXI_DUT_arvalid;
  input [39:0]AXI_DUT_awaddr;
  input [1:0]AXI_DUT_awburst;
  input [3:0]AXI_DUT_awcache;
  input [3:0]AXI_DUT_awid;
  input [7:0]AXI_DUT_awlen;
  input [0:0]AXI_DUT_awlock;
  input [2:0]AXI_DUT_awprot;
  input [3:0]AXI_DUT_awqos;
  output AXI_DUT_awready;
  input [2:0]AXI_DUT_awsize;
  input [0:0]AXI_DUT_awuser;
  input AXI_DUT_awvalid;
  output [3:0]AXI_DUT_bid;
  input AXI_DUT_bready;
  output [1:0]AXI_DUT_bresp;
  output AXI_DUT_bvalid;
  output [31:0]AXI_DUT_rdata;
  output [3:0]AXI_DUT_rid;
  output AXI_DUT_rlast;
  input AXI_DUT_rready;
  output [1:0]AXI_DUT_rresp;
  output AXI_DUT_rvalid;
  input [31:0]AXI_DUT_wdata;
  input AXI_DUT_wlast;
  output AXI_DUT_wready;
  input [3:0]AXI_DUT_wstrb;
  input AXI_DUT_wvalid;
  input [39:0]AXI_MEM_araddr;
  input [1:0]AXI_MEM_arburst;
  input [3:0]AXI_MEM_arcache;
  input [3:0]AXI_MEM_arid;
  input [7:0]AXI_MEM_arlen;
  input [0:0]AXI_MEM_arlock;
  input [2:0]AXI_MEM_arprot;
  input [3:0]AXI_MEM_arqos;
  output AXI_MEM_arready;
  input [2:0]AXI_MEM_arsize;
  input [0:0]AXI_MEM_aruser;
  input AXI_MEM_arvalid;
  input [39:0]AXI_MEM_awaddr;
  input [1:0]AXI_MEM_awburst;
  input [3:0]AXI_MEM_awcache;
  input [3:0]AXI_MEM_awid;
  input [7:0]AXI_MEM_awlen;
  input [0:0]AXI_MEM_awlock;
  input [2:0]AXI_MEM_awprot;
  input [3:0]AXI_MEM_awqos;
  output AXI_MEM_awready;
  input [2:0]AXI_MEM_awsize;
  input [0:0]AXI_MEM_awuser;
  input AXI_MEM_awvalid;
  output [3:0]AXI_MEM_bid;
  input AXI_MEM_bready;
  output [1:0]AXI_MEM_bresp;
  output AXI_MEM_bvalid;
  output [63:0]AXI_MEM_rdata;
  output [3:0]AXI_MEM_rid;
  output AXI_MEM_rlast;
  input AXI_MEM_rready;
  output [1:0]AXI_MEM_rresp;
  output AXI_MEM_rvalid;
  input [63:0]AXI_MEM_wdata;
  input AXI_MEM_wlast;
  output AXI_MEM_wready;
  input [7:0]AXI_MEM_wstrb;
  input AXI_MEM_wvalid;
  input [39:0]AXI_MMIO_araddr;
  input [1:0]AXI_MMIO_arburst;
  input [3:0]AXI_MMIO_arcache;
  input [7:0]AXI_MMIO_arid;
  input [7:0]AXI_MMIO_arlen;
  input [0:0]AXI_MMIO_arlock;
  input [2:0]AXI_MMIO_arprot;
  input [3:0]AXI_MMIO_arqos;
  output [0:0]AXI_MMIO_arready;
  input [2:0]AXI_MMIO_arsize;
  input [0:0]AXI_MMIO_arvalid;
  input [39:0]AXI_MMIO_awaddr;
  input [1:0]AXI_MMIO_awburst;
  input [3:0]AXI_MMIO_awcache;
  input [7:0]AXI_MMIO_awid;
  input [7:0]AXI_MMIO_awlen;
  input [0:0]AXI_MMIO_awlock;
  input [2:0]AXI_MMIO_awprot;
  input [3:0]AXI_MMIO_awqos;
  output [0:0]AXI_MMIO_awready;
  input [2:0]AXI_MMIO_awsize;
  input [0:0]AXI_MMIO_awvalid;
  output [7:0]AXI_MMIO_bid;
  input [0:0]AXI_MMIO_bready;
  output [1:0]AXI_MMIO_bresp;
  output [0:0]AXI_MMIO_bvalid;
  output [63:0]AXI_MMIO_rdata;
  output [7:0]AXI_MMIO_rid;
  output [0:0]AXI_MMIO_rlast;
  input [0:0]AXI_MMIO_rready;
  output [1:0]AXI_MMIO_rresp;
  output [0:0]AXI_MMIO_rvalid;
  input [63:0]AXI_MMIO_wdata;
  input [0:0]AXI_MMIO_wlast;
  output [0:0]AXI_MMIO_wready;
  input [7:0]AXI_MMIO_wstrb;
  input [0:0]AXI_MMIO_wvalid;
  input [0:0]CLK_IN_D_clk_n;
  input [0:0]CLK_IN_D_clk_p;
  output core_clk;
  output [0:0]corerstn;
  output [4:0]intrs;
  input [0:0]pcie_mgt_rxn;
  input [0:0]pcie_mgt_rxp;
  output [0:0]pcie_mgt_txn;
  output [0:0]pcie_mgt_txp;
  output uncore_clk;
  output [0:0]uncorerstn;

  wire [48:0]AXI_Corpus_araddr;
  wire [1:0]AXI_Corpus_arburst;
  wire [3:0]AXI_Corpus_arcache;
  wire [5:0]AXI_Corpus_arid;
  wire [7:0]AXI_Corpus_arlen;
  wire AXI_Corpus_arlock;
  wire [2:0]AXI_Corpus_arprot;
  wire [3:0]AXI_Corpus_arqos;
  wire AXI_Corpus_arready;
  wire [2:0]AXI_Corpus_arsize;
  wire AXI_Corpus_aruser;
  wire AXI_Corpus_arvalid;
  wire [48:0]AXI_Corpus_awaddr;
  wire [1:0]AXI_Corpus_awburst;
  wire [3:0]AXI_Corpus_awcache;
  wire [5:0]AXI_Corpus_awid;
  wire [7:0]AXI_Corpus_awlen;
  wire AXI_Corpus_awlock;
  wire [2:0]AXI_Corpus_awprot;
  wire [3:0]AXI_Corpus_awqos;
  wire AXI_Corpus_awready;
  wire [2:0]AXI_Corpus_awsize;
  wire AXI_Corpus_awuser;
  wire AXI_Corpus_awvalid;
  wire [5:0]AXI_Corpus_bid;
  wire AXI_Corpus_bready;
  wire [1:0]AXI_Corpus_bresp;
  wire AXI_Corpus_bvalid;
  wire [63:0]AXI_Corpus_rdata;
  wire [5:0]AXI_Corpus_rid;
  wire AXI_Corpus_rlast;
  wire AXI_Corpus_rready;
  wire [1:0]AXI_Corpus_rresp;
  wire AXI_Corpus_rvalid;
  wire [63:0]AXI_Corpus_wdata;
  wire AXI_Corpus_wlast;
  wire AXI_Corpus_wready;
  wire [7:0]AXI_Corpus_wstrb;
  wire AXI_Corpus_wvalid;
  wire [39:0]AXI_DMA_araddr;
  wire [1:0]AXI_DMA_arburst;
  wire [3:0]AXI_DMA_arcache;
  wire [6:0]AXI_DMA_arid;
  wire [7:0]AXI_DMA_arlen;
  wire [0:0]AXI_DMA_arlock;
  wire [2:0]AXI_DMA_arprot;
  wire [3:0]AXI_DMA_arqos;
  wire [0:0]AXI_DMA_arready;
  wire [3:0]AXI_DMA_arregion;
  wire [2:0]AXI_DMA_arsize;
  wire [0:0]AXI_DMA_arvalid;
  wire [39:0]AXI_DMA_awaddr;
  wire [1:0]AXI_DMA_awburst;
  wire [3:0]AXI_DMA_awcache;
  wire [6:0]AXI_DMA_awid;
  wire [7:0]AXI_DMA_awlen;
  wire [0:0]AXI_DMA_awlock;
  wire [2:0]AXI_DMA_awprot;
  wire [3:0]AXI_DMA_awqos;
  wire [0:0]AXI_DMA_awready;
  wire [3:0]AXI_DMA_awregion;
  wire [2:0]AXI_DMA_awsize;
  wire [0:0]AXI_DMA_awvalid;
  wire [6:0]AXI_DMA_bid;
  wire [0:0]AXI_DMA_bready;
  wire [1:0]AXI_DMA_bresp;
  wire [0:0]AXI_DMA_bvalid;
  wire [63:0]AXI_DMA_rdata;
  wire [6:0]AXI_DMA_rid;
  wire [0:0]AXI_DMA_rlast;
  wire [0:0]AXI_DMA_rready;
  wire [1:0]AXI_DMA_rresp;
  wire [0:0]AXI_DMA_rvalid;
  wire [63:0]AXI_DMA_wdata;
  wire [0:0]AXI_DMA_wlast;
  wire [0:0]AXI_DMA_wready;
  wire [7:0]AXI_DMA_wstrb;
  wire [0:0]AXI_DMA_wvalid;
  wire [39:0]AXI_DUT_araddr;
  wire [1:0]AXI_DUT_arburst;
  wire [3:0]AXI_DUT_arcache;
  wire [3:0]AXI_DUT_arid;
  wire [7:0]AXI_DUT_arlen;
  wire [0:0]AXI_DUT_arlock;
  wire [2:0]AXI_DUT_arprot;
  wire [3:0]AXI_DUT_arqos;
  wire AXI_DUT_arready;
  wire [2:0]AXI_DUT_arsize;
  wire [0:0]AXI_DUT_aruser;
  wire AXI_DUT_arvalid;
  wire [39:0]AXI_DUT_awaddr;
  wire [1:0]AXI_DUT_awburst;
  wire [3:0]AXI_DUT_awcache;
  wire [3:0]AXI_DUT_awid;
  wire [7:0]AXI_DUT_awlen;
  wire [0:0]AXI_DUT_awlock;
  wire [2:0]AXI_DUT_awprot;
  wire [3:0]AXI_DUT_awqos;
  wire AXI_DUT_awready;
  wire [2:0]AXI_DUT_awsize;
  wire [0:0]AXI_DUT_awuser;
  wire AXI_DUT_awvalid;
  wire [3:0]AXI_DUT_bid;
  wire AXI_DUT_bready;
  wire [1:0]AXI_DUT_bresp;
  wire AXI_DUT_bvalid;
  wire [31:0]AXI_DUT_rdata;
  wire [3:0]AXI_DUT_rid;
  wire AXI_DUT_rlast;
  wire AXI_DUT_rready;
  wire [1:0]AXI_DUT_rresp;
  wire AXI_DUT_rvalid;
  wire [31:0]AXI_DUT_wdata;
  wire AXI_DUT_wlast;
  wire AXI_DUT_wready;
  wire [3:0]AXI_DUT_wstrb;
  wire AXI_DUT_wvalid;
  wire [39:0]AXI_MEM_araddr;
  wire [1:0]AXI_MEM_arburst;
  wire [3:0]AXI_MEM_arcache;
  wire [3:0]AXI_MEM_arid;
  wire [7:0]AXI_MEM_arlen;
  wire [0:0]AXI_MEM_arlock;
  wire [2:0]AXI_MEM_arprot;
  wire [3:0]AXI_MEM_arqos;
  wire AXI_MEM_arready;
  wire [2:0]AXI_MEM_arsize;
  wire [0:0]AXI_MEM_aruser;
  wire AXI_MEM_arvalid;
  wire [39:0]AXI_MEM_awaddr;
  wire [1:0]AXI_MEM_awburst;
  wire [3:0]AXI_MEM_awcache;
  wire [3:0]AXI_MEM_awid;
  wire [7:0]AXI_MEM_awlen;
  wire [0:0]AXI_MEM_awlock;
  wire [2:0]AXI_MEM_awprot;
  wire [3:0]AXI_MEM_awqos;
  wire AXI_MEM_awready;
  wire [2:0]AXI_MEM_awsize;
  wire [0:0]AXI_MEM_awuser;
  wire AXI_MEM_awvalid;
  wire [3:0]AXI_MEM_bid;
  wire AXI_MEM_bready;
  wire [1:0]AXI_MEM_bresp;
  wire AXI_MEM_bvalid;
  wire [63:0]AXI_MEM_rdata;
  wire [3:0]AXI_MEM_rid;
  wire AXI_MEM_rlast;
  wire AXI_MEM_rready;
  wire [1:0]AXI_MEM_rresp;
  wire AXI_MEM_rvalid;
  wire [63:0]AXI_MEM_wdata;
  wire AXI_MEM_wlast;
  wire AXI_MEM_wready;
  wire [7:0]AXI_MEM_wstrb;
  wire AXI_MEM_wvalid;
  wire [39:0]AXI_MMIO_araddr;
  wire [1:0]AXI_MMIO_arburst;
  wire [3:0]AXI_MMIO_arcache;
  wire [7:0]AXI_MMIO_arid;
  wire [7:0]AXI_MMIO_arlen;
  wire [0:0]AXI_MMIO_arlock;
  wire [2:0]AXI_MMIO_arprot;
  wire [3:0]AXI_MMIO_arqos;
  wire [0:0]AXI_MMIO_arready;
  wire [2:0]AXI_MMIO_arsize;
  wire [0:0]AXI_MMIO_arvalid;
  wire [39:0]AXI_MMIO_awaddr;
  wire [1:0]AXI_MMIO_awburst;
  wire [3:0]AXI_MMIO_awcache;
  wire [7:0]AXI_MMIO_awid;
  wire [7:0]AXI_MMIO_awlen;
  wire [0:0]AXI_MMIO_awlock;
  wire [2:0]AXI_MMIO_awprot;
  wire [3:0]AXI_MMIO_awqos;
  wire [0:0]AXI_MMIO_awready;
  wire [2:0]AXI_MMIO_awsize;
  wire [0:0]AXI_MMIO_awvalid;
  wire [7:0]AXI_MMIO_bid;
  wire [0:0]AXI_MMIO_bready;
  wire [1:0]AXI_MMIO_bresp;
  wire [0:0]AXI_MMIO_bvalid;
  wire [63:0]AXI_MMIO_rdata;
  wire [7:0]AXI_MMIO_rid;
  wire [0:0]AXI_MMIO_rlast;
  wire [0:0]AXI_MMIO_rready;
  wire [1:0]AXI_MMIO_rresp;
  wire [0:0]AXI_MMIO_rvalid;
  wire [63:0]AXI_MMIO_wdata;
  wire [0:0]AXI_MMIO_wlast;
  wire [0:0]AXI_MMIO_wready;
  wire [7:0]AXI_MMIO_wstrb;
  wire [0:0]AXI_MMIO_wvalid;
  wire [0:0]CLK_IN_D_clk_n;
  wire [0:0]CLK_IN_D_clk_p;
  wire core_clk;
  wire [0:0]corerstn;
  wire [4:0]intrs;
  wire [0:0]pcie_mgt_rxn;
  wire [0:0]pcie_mgt_rxp;
  wire [0:0]pcie_mgt_txn;
  wire [0:0]pcie_mgt_txp;
  wire uncore_clk;
  wire [0:0]uncorerstn;

  zynq_soc zynq_soc_i
       (.AXI_Corpus_araddr(AXI_Corpus_araddr),
        .AXI_Corpus_arburst(AXI_Corpus_arburst),
        .AXI_Corpus_arcache(AXI_Corpus_arcache),
        .AXI_Corpus_arid(AXI_Corpus_arid),
        .AXI_Corpus_arlen(AXI_Corpus_arlen),
        .AXI_Corpus_arlock(AXI_Corpus_arlock),
        .AXI_Corpus_arprot(AXI_Corpus_arprot),
        .AXI_Corpus_arqos(AXI_Corpus_arqos),
        .AXI_Corpus_arready(AXI_Corpus_arready),
        .AXI_Corpus_arsize(AXI_Corpus_arsize),
        .AXI_Corpus_aruser(AXI_Corpus_aruser),
        .AXI_Corpus_arvalid(AXI_Corpus_arvalid),
        .AXI_Corpus_awaddr(AXI_Corpus_awaddr),
        .AXI_Corpus_awburst(AXI_Corpus_awburst),
        .AXI_Corpus_awcache(AXI_Corpus_awcache),
        .AXI_Corpus_awid(AXI_Corpus_awid),
        .AXI_Corpus_awlen(AXI_Corpus_awlen),
        .AXI_Corpus_awlock(AXI_Corpus_awlock),
        .AXI_Corpus_awprot(AXI_Corpus_awprot),
        .AXI_Corpus_awqos(AXI_Corpus_awqos),
        .AXI_Corpus_awready(AXI_Corpus_awready),
        .AXI_Corpus_awsize(AXI_Corpus_awsize),
        .AXI_Corpus_awuser(AXI_Corpus_awuser),
        .AXI_Corpus_awvalid(AXI_Corpus_awvalid),
        .AXI_Corpus_bid(AXI_Corpus_bid),
        .AXI_Corpus_bready(AXI_Corpus_bready),
        .AXI_Corpus_bresp(AXI_Corpus_bresp),
        .AXI_Corpus_bvalid(AXI_Corpus_bvalid),
        .AXI_Corpus_rdata(AXI_Corpus_rdata),
        .AXI_Corpus_rid(AXI_Corpus_rid),
        .AXI_Corpus_rlast(AXI_Corpus_rlast),
        .AXI_Corpus_rready(AXI_Corpus_rready),
        .AXI_Corpus_rresp(AXI_Corpus_rresp),
        .AXI_Corpus_rvalid(AXI_Corpus_rvalid),
        .AXI_Corpus_wdata(AXI_Corpus_wdata),
        .AXI_Corpus_wlast(AXI_Corpus_wlast),
        .AXI_Corpus_wready(AXI_Corpus_wready),
        .AXI_Corpus_wstrb(AXI_Corpus_wstrb),
        .AXI_Corpus_wvalid(AXI_Corpus_wvalid),
        .AXI_DMA_araddr(AXI_DMA_araddr),
        .AXI_DMA_arburst(AXI_DMA_arburst),
        .AXI_DMA_arcache(AXI_DMA_arcache),
        .AXI_DMA_arid(AXI_DMA_arid),
        .AXI_DMA_arlen(AXI_DMA_arlen),
        .AXI_DMA_arlock(AXI_DMA_arlock),
        .AXI_DMA_arprot(AXI_DMA_arprot),
        .AXI_DMA_arqos(AXI_DMA_arqos),
        .AXI_DMA_arready(AXI_DMA_arready),
        .AXI_DMA_arregion(AXI_DMA_arregion),
        .AXI_DMA_arsize(AXI_DMA_arsize),
        .AXI_DMA_arvalid(AXI_DMA_arvalid),
        .AXI_DMA_awaddr(AXI_DMA_awaddr),
        .AXI_DMA_awburst(AXI_DMA_awburst),
        .AXI_DMA_awcache(AXI_DMA_awcache),
        .AXI_DMA_awid(AXI_DMA_awid),
        .AXI_DMA_awlen(AXI_DMA_awlen),
        .AXI_DMA_awlock(AXI_DMA_awlock),
        .AXI_DMA_awprot(AXI_DMA_awprot),
        .AXI_DMA_awqos(AXI_DMA_awqos),
        .AXI_DMA_awready(AXI_DMA_awready),
        .AXI_DMA_awregion(AXI_DMA_awregion),
        .AXI_DMA_awsize(AXI_DMA_awsize),
        .AXI_DMA_awvalid(AXI_DMA_awvalid),
        .AXI_DMA_bid(AXI_DMA_bid),
        .AXI_DMA_bready(AXI_DMA_bready),
        .AXI_DMA_bresp(AXI_DMA_bresp),
        .AXI_DMA_bvalid(AXI_DMA_bvalid),
        .AXI_DMA_rdata(AXI_DMA_rdata),
        .AXI_DMA_rid(AXI_DMA_rid),
        .AXI_DMA_rlast(AXI_DMA_rlast),
        .AXI_DMA_rready(AXI_DMA_rready),
        .AXI_DMA_rresp(AXI_DMA_rresp),
        .AXI_DMA_rvalid(AXI_DMA_rvalid),
        .AXI_DMA_wdata(AXI_DMA_wdata),
        .AXI_DMA_wlast(AXI_DMA_wlast),
        .AXI_DMA_wready(AXI_DMA_wready),
        .AXI_DMA_wstrb(AXI_DMA_wstrb),
        .AXI_DMA_wvalid(AXI_DMA_wvalid),
        .AXI_DUT_araddr(AXI_DUT_araddr),
        .AXI_DUT_arburst(AXI_DUT_arburst),
        .AXI_DUT_arcache(AXI_DUT_arcache),
        .AXI_DUT_arid(AXI_DUT_arid),
        .AXI_DUT_arlen(AXI_DUT_arlen),
        .AXI_DUT_arlock(AXI_DUT_arlock),
        .AXI_DUT_arprot(AXI_DUT_arprot),
        .AXI_DUT_arqos(AXI_DUT_arqos),
        .AXI_DUT_arready(AXI_DUT_arready),
        .AXI_DUT_arsize(AXI_DUT_arsize),
        .AXI_DUT_aruser(AXI_DUT_aruser),
        .AXI_DUT_arvalid(AXI_DUT_arvalid),
        .AXI_DUT_awaddr(AXI_DUT_awaddr),
        .AXI_DUT_awburst(AXI_DUT_awburst),
        .AXI_DUT_awcache(AXI_DUT_awcache),
        .AXI_DUT_awid(AXI_DUT_awid),
        .AXI_DUT_awlen(AXI_DUT_awlen),
        .AXI_DUT_awlock(AXI_DUT_awlock),
        .AXI_DUT_awprot(AXI_DUT_awprot),
        .AXI_DUT_awqos(AXI_DUT_awqos),
        .AXI_DUT_awready(AXI_DUT_awready),
        .AXI_DUT_awsize(AXI_DUT_awsize),
        .AXI_DUT_awuser(AXI_DUT_awuser),
        .AXI_DUT_awvalid(AXI_DUT_awvalid),
        .AXI_DUT_bid(AXI_DUT_bid),
        .AXI_DUT_bready(AXI_DUT_bready),
        .AXI_DUT_bresp(AXI_DUT_bresp),
        .AXI_DUT_bvalid(AXI_DUT_bvalid),
        .AXI_DUT_rdata(AXI_DUT_rdata),
        .AXI_DUT_rid(AXI_DUT_rid),
        .AXI_DUT_rlast(AXI_DUT_rlast),
        .AXI_DUT_rready(AXI_DUT_rready),
        .AXI_DUT_rresp(AXI_DUT_rresp),
        .AXI_DUT_rvalid(AXI_DUT_rvalid),
        .AXI_DUT_wdata(AXI_DUT_wdata),
        .AXI_DUT_wlast(AXI_DUT_wlast),
        .AXI_DUT_wready(AXI_DUT_wready),
        .AXI_DUT_wstrb(AXI_DUT_wstrb),
        .AXI_DUT_wvalid(AXI_DUT_wvalid),
        .AXI_MEM_araddr(AXI_MEM_araddr),
        .AXI_MEM_arburst(AXI_MEM_arburst),
        .AXI_MEM_arcache(AXI_MEM_arcache),
        .AXI_MEM_arid(AXI_MEM_arid),
        .AXI_MEM_arlen(AXI_MEM_arlen),
        .AXI_MEM_arlock(AXI_MEM_arlock),
        .AXI_MEM_arprot(AXI_MEM_arprot),
        .AXI_MEM_arqos(AXI_MEM_arqos),
        .AXI_MEM_arready(AXI_MEM_arready),
        .AXI_MEM_arsize(AXI_MEM_arsize),
        .AXI_MEM_aruser(AXI_MEM_aruser),
        .AXI_MEM_arvalid(AXI_MEM_arvalid),
        .AXI_MEM_awaddr(AXI_MEM_awaddr),
        .AXI_MEM_awburst(AXI_MEM_awburst),
        .AXI_MEM_awcache(AXI_MEM_awcache),
        .AXI_MEM_awid(AXI_MEM_awid),
        .AXI_MEM_awlen(AXI_MEM_awlen),
        .AXI_MEM_awlock(AXI_MEM_awlock),
        .AXI_MEM_awprot(AXI_MEM_awprot),
        .AXI_MEM_awqos(AXI_MEM_awqos),
        .AXI_MEM_awready(AXI_MEM_awready),
        .AXI_MEM_awsize(AXI_MEM_awsize),
        .AXI_MEM_awuser(AXI_MEM_awuser),
        .AXI_MEM_awvalid(AXI_MEM_awvalid),
        .AXI_MEM_bid(AXI_MEM_bid),
        .AXI_MEM_bready(AXI_MEM_bready),
        .AXI_MEM_bresp(AXI_MEM_bresp),
        .AXI_MEM_bvalid(AXI_MEM_bvalid),
        .AXI_MEM_rdata(AXI_MEM_rdata),
        .AXI_MEM_rid(AXI_MEM_rid),
        .AXI_MEM_rlast(AXI_MEM_rlast),
        .AXI_MEM_rready(AXI_MEM_rready),
        .AXI_MEM_rresp(AXI_MEM_rresp),
        .AXI_MEM_rvalid(AXI_MEM_rvalid),
        .AXI_MEM_wdata(AXI_MEM_wdata),
        .AXI_MEM_wlast(AXI_MEM_wlast),
        .AXI_MEM_wready(AXI_MEM_wready),
        .AXI_MEM_wstrb(AXI_MEM_wstrb),
        .AXI_MEM_wvalid(AXI_MEM_wvalid),
        .AXI_MMIO_araddr(AXI_MMIO_araddr),
        .AXI_MMIO_arburst(AXI_MMIO_arburst),
        .AXI_MMIO_arcache(AXI_MMIO_arcache),
        .AXI_MMIO_arid(AXI_MMIO_arid),
        .AXI_MMIO_arlen(AXI_MMIO_arlen),
        .AXI_MMIO_arlock(AXI_MMIO_arlock),
        .AXI_MMIO_arprot(AXI_MMIO_arprot),
        .AXI_MMIO_arqos(AXI_MMIO_arqos),
        .AXI_MMIO_arready(AXI_MMIO_arready),
        .AXI_MMIO_arsize(AXI_MMIO_arsize),
        .AXI_MMIO_arvalid(AXI_MMIO_arvalid),
        .AXI_MMIO_awaddr(AXI_MMIO_awaddr),
        .AXI_MMIO_awburst(AXI_MMIO_awburst),
        .AXI_MMIO_awcache(AXI_MMIO_awcache),
        .AXI_MMIO_awid(AXI_MMIO_awid),
        .AXI_MMIO_awlen(AXI_MMIO_awlen),
        .AXI_MMIO_awlock(AXI_MMIO_awlock),
        .AXI_MMIO_awprot(AXI_MMIO_awprot),
        .AXI_MMIO_awqos(AXI_MMIO_awqos),
        .AXI_MMIO_awready(AXI_MMIO_awready),
        .AXI_MMIO_awsize(AXI_MMIO_awsize),
        .AXI_MMIO_awvalid(AXI_MMIO_awvalid),
        .AXI_MMIO_bid(AXI_MMIO_bid),
        .AXI_MMIO_bready(AXI_MMIO_bready),
        .AXI_MMIO_bresp(AXI_MMIO_bresp),
        .AXI_MMIO_bvalid(AXI_MMIO_bvalid),
        .AXI_MMIO_rdata(AXI_MMIO_rdata),
        .AXI_MMIO_rid(AXI_MMIO_rid),
        .AXI_MMIO_rlast(AXI_MMIO_rlast),
        .AXI_MMIO_rready(AXI_MMIO_rready),
        .AXI_MMIO_rresp(AXI_MMIO_rresp),
        .AXI_MMIO_rvalid(AXI_MMIO_rvalid),
        .AXI_MMIO_wdata(AXI_MMIO_wdata),
        .AXI_MMIO_wlast(AXI_MMIO_wlast),
        .AXI_MMIO_wready(AXI_MMIO_wready),
        .AXI_MMIO_wstrb(AXI_MMIO_wstrb),
        .AXI_MMIO_wvalid(AXI_MMIO_wvalid),
        .CLK_IN_D_clk_n(CLK_IN_D_clk_n),
        .CLK_IN_D_clk_p(CLK_IN_D_clk_p),
        .core_clk(core_clk),
        .corerstn(corerstn),
        .intrs(intrs),
        .pcie_mgt_rxn(pcie_mgt_rxn),
        .pcie_mgt_rxp(pcie_mgt_rxp),
        .pcie_mgt_txn(pcie_mgt_txn),
        .pcie_mgt_txp(pcie_mgt_txp),
        .uncore_clk(uncore_clk),
        .uncorerstn(uncorerstn));
endmodule
