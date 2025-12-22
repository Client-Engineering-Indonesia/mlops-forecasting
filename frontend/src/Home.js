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

  const [projects, setProjects] = useState([]);
  const [error, setError] = useState(null);

  const [loading, setLoading] = useState(false);

  const [projectName, setProjectName] = useState("");
  const [projectDescription, setProjectDescription] = useState("");

  async function listProjects() {
    setLoading(true);
    const response = await fetch(BE_URL + "/list_projects");

    if (!response.ok) {
      throw new Error("Failed to fetch projects");
    }

    setLoading(false);

    return await response.json();
  }

  useEffect(() => {
    listProjects()
      .then(setProjects)
      .catch(err => setError(err.message));
  }, []);

  if (error) return <p>Error: {error}</p>;

  async function createProject(e) {
    e.preventDefault(); // prevent page reload
    setLoading(true);
    setError(null);

    try {
      const response = await fetch(`${BE_URL}/create_project`, {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
        },
        body: JSON.stringify({
          project_name: projectName,
          project_description: projectDescription,
        }),
      });

      if (!response.ok) {
        throw new Error("Failed to create project");
      }

      // Clear form
      setProjectName("");
      setProjectDescription("");

      // Refresh list
      const updatedProjects = await listProjects();
      setProjects(updatedProjects);

    } catch (err) {
      setError(err.message);
    } finally {
      setLoading(false);
    }
  }

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

          <Form onSubmit={createProject}>
            <Stack gap={7}>
              <FormGroup legendText="Input project details here">
                <TextInput
                  id="project-name"
                  labelText="Project Name"
                  placeholder="Project Name"
                  value={projectName}
                  onChange={(e) => setProjectName(e.target.value)}
                />

                <TextArea
                  id="project-description"
                  labelText="Project Description"
                  placeholder="Project Description"
                  rows={4}
                  value={projectDescription}
                  onChange={(e) => setProjectDescription(e.target.value)}
                />
              </FormGroup>

              <Button type="submit" className="some-class">
                Submit
              </Button>

            </Stack>

          </Form>
        </div>
      </div>

      {loading == true && (
        <Loading
          active
          className="some-class"
          description="Loading"
          withOverlay={loading}
        />
      )}

      

      

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
              {projects.map((p, i) => (
                <TableRow>
                  <TableCell>{p.project_id}</TableCell>
                  <TableCell>{p.project_name}</TableCell>
                  <TableCell>{p.project_description}</TableCell>
                  <TableCell>{p.creation_date}</TableCell>
                  <TableCell>
                    <Link href={`/project?project_id=${p.project_id}`}>View</Link>
                  </TableCell>
              </TableRow>
              ))}
              
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