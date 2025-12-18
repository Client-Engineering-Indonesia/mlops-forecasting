import {
    Accordion,
    AccordionItem,
    Breadcrumb,
    TextInput,
    TextArea,
    Form,
    Stack,
    FormGroup,
    ContainedList,
    ContainedListItem,
    CheckboxGroup,
    Checkbox,
    Select,
    SelectItem,
    NumberInput,
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
    Dropdown,
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


import './Features.css'


import { useNavigate } from 'react-router-dom';
import axios from 'axios';


function Features() {

    const BE_URL = process.env.REACT_APP_API_URL;
    //console.log("BE_URL: " + BE_URL); // should print http://localhost:8000

    return (
        <div className="sub-main-page">
            <div className="overview" style={{ display: 'flex', justifyContent: 'center' }}>

                <div className='form-group'>

                    <h3>CREATE NEW FEATURE SET</h3>

                    <Form>
                        <Stack gap={7}>
                            <FormGroup legendText="Input feature details here">
                                <div>
                                    <Select
                                        id="select-1"
                                        labelText="Select a dataset"
                                        size="md"
                                    >
                                        <SelectItem
                                            text=""
                                            value=""
                                        />
                                        <SelectItem
                                            text="An example option that is really long to show what should be done to handle long text"
                                            value="An example option that is really long to show what should be done to handle long text"
                                        />
                                        <SelectItem
                                            text="Option 2"
                                            value="option-2"
                                        />
                                        <SelectItem
                                            text="Option 3"
                                            value="option-3"
                                        />
                                        <SelectItem
                                            text="Option 4"
                                            value="option-4"
                                        />
                                    </Select>
                                </div>
                            </FormGroup>

                            <Button type="submit" className="some-class">
                                Submit
                            </Button>

                        </Stack>

                    </Form>
                </div>

                <div className='form-group'>

                    <h3>LIST OF FEATURE SETS</h3>



                    <Accordion>
                        <AccordionItem title="Feature Set 1">

                            <p>
                                <b>Created At</b>: 2025-01-01 10:00:00
                            </p>
                            <p>
                                <b>Total Features</b>: 10
                            </p>
                            
                            <ContainedList label="Features">
                                {[...Array(4)].map((_, i) => <ContainedListItem key={i}>
                                    <div style={{
                                        display: 'grid',
                                        gridTemplateColumns: 'repeat(5, 1fr)',
                                        columnGap: '1rem'
                                    }}>
                                        <span>Feature Name</span>
                                        <span>Feature Description</span>
                                        
                                    </div>
                                </ContainedListItem>)}
                            </ContainedList>




                        </AccordionItem>
                    </Accordion>


                </div>
            </div>

        </div>
    );
}

export default Features;