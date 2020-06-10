import React from 'react';
import Modal from 'react-bootstrap/lib/Modal';

import Button from 'app/components/button';
import ButtonBar from 'app/components/buttonBar';
import {t} from 'app/locale';

import {StyledModal} from './styles';

type Props = {
  onClose: () => void;
  onSave: () => void;
  title: string;
  content: React.ReactElement;
  disabled: boolean;
  open: boolean;
};

const Dialog = ({onClose, open, title, onSave, content, disabled}: Props) => (
  <StyledModal show={open} animation={false} onHide={onClose}>
    <Modal.Header closeButton>{title}</Modal.Header>
    <Modal.Body>{content}</Modal.Body>
    <Modal.Footer>
      <ButtonBar gap={1.5}>
        <Button onClick={onClose}>{t('Cancel')}</Button>
        <Button onClick={onSave} disabled={disabled} priority="primary">
          {t('Save Relay')}
        </Button>
      </ButtonBar>
    </Modal.Footer>
  </StyledModal>
);

export default Dialog;
