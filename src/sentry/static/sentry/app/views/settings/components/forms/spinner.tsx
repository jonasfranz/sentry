import {keyframes} from '@emotion/core';
import styled from '@emotion/styled';

const spin = keyframes`
  0% {
    transform: rotate(0deg);
  }
  100% {
    transform: rotate(360deg);
  }
`;

const Spinner = styled('div')`
  animation: ${spin} 0.4s linear infinite;
  width: 18px;
  height: 18px;
  border-radius: 18px;
  border-top: 2px solid ${p => p.theme.gray300};
  border-right: 2px solid ${p => p.theme.gray300};
  border-bottom: 2px solid ${p => p.theme.gray300};
  border-left: 2px solid ${p => p.theme.purple400};
  margin-left: auto;
`;

export default Spinner;
