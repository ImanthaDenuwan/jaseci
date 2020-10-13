import React, { Component } from "react";
import WktItemList from "./wkt-item-list";
import { Container } from "react-bootstrap";

class WktNotes extends Component {
  wkt_note(w) {
    const ctx = w.context;
    const is_open = ctx.status === "open" || !ctx.status;
    if (ctx.wtype && ctx.wtype === "note" && is_open) return true;
    return false;
  }

  render() {
    return (
      <Container fluid>
        <WktItemList
          filter_func={this.wkt_note}
          w_id={this.props.w_id}
          color="#eeeeee"
        />
      </Container>
    );
  }
}

export default WktNotes;