import {
  Breadcrumb,
  TextInput,
  TextArea,
  Form,
  Stack,
  FormGroup,
  BreadcrumbItem,
  DataTable,
  Link,
  Table,
  TableHead,
  TableRow,
  TableHeader,
  TableBody,
  TableCell,
  TableToolbar,
  TableContainer,
  TableToolbarSearch,
  Button,
  Callout,
  Loading,
  unstable__IconIndicator as IconIndicator,
} from '@carbon/react';
import React, { useState, useEffect } from 'react';
import {
  Add,
  View,
  AiLaunch,
  TrashCan,
  Notification
} from '@carbon/icons-react';

import TradeOperationAssistant from './components/TradeOperationAssistant/TradeOperationAssistant'

import './Home.css'


import { useNavigate } from 'react-router-dom';
import axios from 'axios';

import HeaderBanner from './assets/top-nav.png'
import IBMLogo from './assets/ibm-logo.png'
import TextBanner from './assets/Banner-Only.png'
import OverviewBanner from './assets/overview-banner.png'


function Home() {

  const BE_URL = process.env.REACT_APP_API_URL;
  //console.log("BE_URL: " + BE_URL); // should print http://localhost:8000

  return (
    <div className="main-page">
      <div className="top-header">
        <img src={HeaderBanner} alt="Header" className="header-banner" />
        <div className="header-sub">
          <img src={IBMLogo} alt="Logo" className="overlay-logo" />
          <span className="header-sub-text">Smart Forecasting Tool</span>
        </div>
        <div className="header-overlay">
          <h1 className="header-title">Faster <span className='header-title-span'>Forecasting Model Development Lifecycle</span> with AI-Embedded Capability</h1>
        </div>

        <img src={TextBanner} style={{ width: '100%', marginTop: '-10px' }} />

      </div>
      <div className="breadcrumb">
        <Breadcrumb>
          <BreadcrumbItem href="/home">Home</BreadcrumbItem>
        </Breadcrumb>
      </div>
      <div className="overview" style={{ display: 'flex', justifyContent: 'center' }}>

        <div className='form-group'>

          <h2>CREATE NEW PROJECT</h2>

          <Form>
            <Stack gap={7}>
              <FormGroup legendText="Input project details here">
                <TextInput id="project-name" labelText="Project Name" placeholder="Project Name" />
                <TextArea labelText="Project Description" placeholder="Project Description" id="project-description" rows={4} />
              </FormGroup>

              <Button type="submit" className="some-class">
                Submit
              </Button>

            </Stack>

          </Form>
        </div>
      </div>

      <div className="overview" style={{ display: 'flex', justifyContent: 'center' }}>

        <div className='form-group'>

          <h2>LIST OF PROJECTS</h2>

          <Table
            aria-label="sample table"
            size="lg"
          >
            <TableHead>
              <TableRow>
                <TableHeader>
                  ID
                </TableHeader>
                <TableHeader>
                  Name
                </TableHeader>
                <TableHeader>
                  Description
                </TableHeader>
                <TableHeader>
                  Creation Time
                </TableHeader>
                <TableHeader>
                  Actions
                </TableHeader>
              </TableRow>
            </TableHead>
            <TableBody>
              <TableRow>
                <TableCell>
                  0000-0000
                </TableCell>
                <TableCell>
                  RPS
                </TableCell>
                <TableCell>
                  Forecast RPS
                </TableCell>
                <TableCell>
                  2025-10-01 10:00:05
                </TableCell>
                <TableCell>
                  <Link href="#">View</Link>
                </TableCell>
              </TableRow>
            </TableBody>
          </Table>
        </div>
      </div>



      <div class="footer">
        Copyright © IBM Corporation 2025
      </div>

    </div>
  );
}

export default Home;