import React from 'react';
import styled from '@emotion/styled';
import {css} from '@emotion/core';

import space from 'app/styles/space';

type Props = {
  label: string;
  children: React.ReactNode;
  isFullWidth?: boolean;
};

const FormField = ({label, children, isFullWidth}: Props) => (
  <Wrapper isFullWidth={isFullWidth}>
    <Label>
      <LabelDescription>{label}</LabelDescription>
    </Label>
    {children}
  </Wrapper>
);

export default FormField;

const Wrapper = styled('div')<{isFullWidth?: boolean}>`
  ${p =>
    p.isFullWidth &&
    css`
      grid-column-start: 1;
      grid-column-end: -1;
    `}
`;

const Label = styled('div')`
  display: flex;
  align-items: center;
  margin-bottom: ${space(0.5)};
`;

const LabelDescription = styled('span')`
  margin-right: ${space(1)};
`;
